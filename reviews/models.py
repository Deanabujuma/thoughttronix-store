from django.conf import settings
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models, transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone

from orders.models import Order, OrderItem
from products.models import Product


def is_regular_customer(user):
    """Signed in, and neither staff nor the admin."""
    return user.is_authenticated and not (user.is_staff or user.is_superuser)


def has_received(user, product):
    """Whether ``user`` has a Delivered order containing this exact
    product record — matched by FK, never by name or slug."""
    return OrderItem.objects.filter(
        product=product,
        order__user=user,
        order__status=Order.Status.DELIVERED,
    ).exists()


class ReviewQuerySet(models.QuerySet):
    def published(self):
        """Only what the public may see.

        Every public list, average and count goes through here, so a
        hidden review drops out everywhere at once.
        """
        return self.filter(status=Review.Status.PUBLISHED)

    def summary_for(self, product):
        """The product's rating summary: ``{"average": …, "count": …}``.

        Published reviews only, in one query. ``average`` is ``None``
        when there are none.
        """
        return (
            self.published()
            .filter(product=product)
            .aggregate(average=Avg("rating"), count=Count("pk"))
        )

    def own(self, user, product):
        """The visitor's own review of ``product``, or ``None``."""
        if not user.is_authenticated:
            return None
        return self.filter(user=user, product=product).first()

    def can_create(self, user, product):
        """Whether ``user`` may write a new review of ``product``.

        Only a regular customer with a Delivered order containing this
        exact product record (matched by FK, never by name) qualifies,
        and only while they have no review of it yet and no restriction
        on it.
        """
        if not is_regular_customer(user):
            return False
        if self.filter(user=user, product=product).exists():
            return False
        if ReviewRestriction.applies(user, product):
            return False
        return has_received(user, product)

    def visitor_state(self, user, product, own_review):
        """Which "Your review" area the product page shows this visitor.

        One of ``"anonymous"``, ``"author"``, ``"staff"`` (shown nothing),
        ``"restricted"``, ``"eligible"`` or ``"ineligible"``. It asks
        ``can_create`` — the same rule the create view enforces — so the
        page never offers what the server would refuse. A restriction is
        the more specific reason, so it wins over "ineligible".
        """
        if not user.is_authenticated:
            return "anonymous"
        if own_review:
            return "author"
        if user.is_staff or user.is_superuser:
            return "staff"
        if ReviewRestriction.applies(user, product):
            return "restricted"
        if self.can_create(user, product):
            return "eligible"
        return "ineligible"


class Review(models.Model):
    """One customer's rating of one product they received.

    Reviews go live at once and are moderated after the fact. ``status``
    is stored on its own and never inferred from ``hidden_by``, which
    becomes NULL if the moderator's account is deleted.
    """

    class Status(models.TextChoices):
        PUBLISHED = "PUBLISHED", "Published"
        HIDDEN = "HIDDEN", "Hidden"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    # TextField's max_length only reaches the form; the validator makes
    # the model enforce it too.
    comment = models.TextField(
        max_length=2000, blank=True, validators=[MaxLengthValidator(2000)]
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PUBLISHED
    )
    hidden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    hidden_at = models.DateTimeField(null=True, blank=True)
    hidden_reason = models.CharField(max_length=200, blank=True)
    # default (not auto_now_add) so the seed can backdate reviews.
    created_at = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(null=True, blank=True)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"], name="unique_review_user_product"
            ),
            models.CheckConstraint(
                condition=Q(rating__gte=1, rating__lte=5),
                name="review_rating_1_to_5",
            ),
            # Hidden always carries its record; published never does.
            # hidden_by is left out on purpose: it can become NULL.
            models.CheckConstraint(
                condition=(
                    Q(status="HIDDEN", hidden_at__isnull=False) & ~Q(hidden_reason="")
                )
                | Q(status="PUBLISHED", hidden_at__isnull=True, hidden_reason=""),
                name="review_hidden_state_consistent",
            ),
        ]

    def __str__(self):
        return f"{self.rating}★ for {self.product.name}"

    def save(self, *args, **kwargs):
        # Trim on every save, so a whitespace-only comment is stored empty.
        self.comment = self.comment.strip()
        super().save(*args, **kwargs)

    def can_edit(self, user):
        """Whether ``user`` may edit this review: its author, while still a
        regular customer with a Delivered order for this product, and only
        while the review is published — staff moderation isn't editable.

        Not ``can_create`` — the review itself makes that false.
        """
        return (
            self.status == self.Status.PUBLISHED
            and self.is_by(user)
            and is_regular_customer(user)
            and has_received(user, self.product)
        )

    def can_delete(self, user):
        """Whether ``user`` may delete this review: its author, always —
        even once hidden, after an order changes, or after promotion."""
        return self.is_by(user)

    def is_by(self, user):
        """Whether ``user`` is this review's signed-in author."""
        return user.is_authenticated and self.user_id == user.pk

    def hide(self, by, reason):
        """Hide this review, recording who hid it, when and why.

        Returns whether it was hidden now. Only a published review changes:
        one conditional UPDATE does the check and the write together, so a
        repeated or concurrent hide can never overwrite the original
        moderator, time or reason.
        """
        hidden = (
            Review.objects.filter(pk=self.pk, status=self.Status.PUBLISHED).update(
                status=self.Status.HIDDEN,
                hidden_by=by,
                hidden_at=timezone.now(),
                hidden_reason=reason,
            )
            == 1
        )
        self.refresh_from_db()
        return hidden

    def restore(self):
        """Publish a hidden review again, clearing its moderation record.

        Returns whether it was restored now. Like ``hide``, one conditional
        UPDATE does the check and the write, so restoring twice — or two
        moderators at once — changes nothing the second time.
        """
        restored = (
            Review.objects.filter(pk=self.pk, status=self.Status.HIDDEN).update(
                status=self.Status.PUBLISHED,
                hidden_by=None,
                hidden_at=None,
                hidden_reason="",
            )
            == 1
        )
        self.refresh_from_db()
        return restored

    def delete_by_author(self):
        """Delete at the author's request — the only path the customer
        delete view uses. The Django admin's own delete stays separate.

        Deleting a hidden review leaves a ``ReviewRestriction`` behind,
        copying staff's record of the hide (never the rating or comment),
        so the author can't simply post again. One restriction per
        customer and product: an existing one is updated, not duplicated.
        The restriction and the deletion happen together or not at all.
        """
        with transaction.atomic():
            if self.status == self.Status.HIDDEN:
                ReviewRestriction.objects.update_or_create(
                    user_id=self.user_id,
                    product_id=self.product_id,
                    defaults={
                        "hidden_reason": self.hidden_reason,
                        "hidden_by_id": self.hidden_by_id,
                        "hidden_at": self.hidden_at,
                        "created_at": timezone.now(),
                    },
                )
            self.delete()


class ReviewRestriction(models.Model):
    """Blocks one customer from reviewing one product again.

    Left behind when an author deletes a hidden review, so moderation
    can't be undone by deleting and reposting. It keeps staff's record of
    the hide — never the review's rating or comment. A row existing means
    the restriction is active; clearing it deletes the row.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_restrictions",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="review_restrictions"
    )
    hidden_reason = models.CharField(max_length=200)
    hidden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    hidden_at = models.DateTimeField()
    # When the author deleted the hidden review.
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"], name="unique_restriction_user_product"
            )
        ]

    def __str__(self):
        return f"{self.user} may not review {self.product}"

    @classmethod
    def applies(cls, user, product):
        """Whether ``user`` is restricted from reviewing ``product``."""
        return cls.objects.filter(user=user, product=product).exists()

    def clear(self):
        """Lift this restriction, so the customer may review again.

        Returns whether it was cleared now. Only this one row is deleted,
        in a single statement, so two staff clearing at once can't
        conflict — the second simply finds nothing left.
        """
        return ReviewRestriction.objects.filter(pk=self.pk).delete()[0] > 0
