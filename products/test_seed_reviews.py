"""The seed's demo reviews (Phase 6 of the product-reviews plan).

Every run happens in pytest's isolated database — never against
db.sqlite3 — and, wherever dates matter, at the baseline test's frozen
clock.
"""

import io
from collections import Counter

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from orders.models import Order, OrderItem
from products.models import Product
from reviews.models import Review, ReviewRestriction, has_received

from .test_seed_baseline import (
    FROZEN_NOW,
    frozen_clock,  # noqa: F401 — the shared fixed clock
)


def delivered_customers(product):
    """Distinct regular customers with a Delivered order of ``product``."""
    return set(
        OrderItem.objects.filter(
            product=product,
            order__status=Order.Status.DELIVERED,
            order__user__is_staff=False,
            order__user__is_superuser=False,
        ).values_list("order__user__username", flat=True)
    )


@pytest.mark.usefixtures("frozen_clock")
def test_seeded_reviews_are_genuine_and_show_every_demo_state(db):
    call_command("seed")

    reviews = list(Review.objects.select_related("user", "product", "hidden_by"))
    assert len(reviews) > 0, "the seed builds demo reviews"

    # Only regular customers who received that exact product, once each.
    for review in reviews:
        author = review.user
        assert not (author.is_staff or author.is_superuser), review
        assert has_received(author, review.product), review
    pairs = [(r.user.username, r.product.slug) for r in reviews]
    assert len(pairs) == len(set(pairs))
    per_product = Counter(r.product_id for r in reviews)
    for product in Product.objects.filter(pk__in=per_product):
        assert per_product[product.pk] <= len(delivered_customers(product))

    # The demo customer's product pages.
    mine = {r.product.slug: r for r in reviews if r.user.username == "customer"}
    assert mine["mindsync"].status == Review.Status.PUBLISHED
    assert mine["mindsync"].edited_at is not None
    assert mine["dreamweaver"].status == Review.Status.HIDDEN
    assert mine["dreamweaver"].hidden_by.username == "employee"
    assert mine["dreamweaver"].hidden_reason
    for unreviewed in ["syncrest", "seraphine-mini", "veil"]:
        assert unreviewed not in mine

    # The background customers: a believable mix.
    background = [r for r in reviews if r.user.username != "customer"]
    assert any(r.status == Review.Status.HIDDEN for r in background)
    assert any(r.edited_at for r in background)
    assert any(r.status == Review.Status.PUBLISHED for r in background)
    assert len({r.rating for r in reviews}) >= 3
    assert any(r.comment for r in reviews) and any(not r.comment for r in reviews)
    assert Product.objects.exclude(reviews__isnull=False).exists()

    # Exactly one restriction, on a background customer who received the
    # product, as if they deleted a review staff hid — so no review remains.
    restrictions = list(ReviewRestriction.objects.select_related("user", "product"))
    assert len(restrictions) == 1
    (restriction,) = restrictions
    assert restriction.user.username != "customer"
    assert has_received(restriction.user, restriction.product)
    assert not Review.objects.filter(
        user=restriction.user, product=restriction.product
    ).exists()
    assert restriction.hidden_by == get_user_model().objects.get(username="employee")
    assert restriction.hidden_reason


# --- Behavior 2: a valid timeline, and the same output every run --------------


def first_delivery(user, product):
    """When the customer's earliest Delivered order of ``product`` was placed."""
    return (
        Order.objects.filter(
            user=user, status=Order.Status.DELIVERED, items__product=product
        )
        .order_by("created_at")
        .values_list("created_at", flat=True)
        .first()
    )


def review_data():
    """Every seeded review and restriction, by natural keys, in a stable order."""
    reviews = [
        (
            r.user.username,
            r.product.slug,
            r.rating,
            r.comment,
            r.status,
            r.hidden_by.username if r.hidden_by else None,
            r.hidden_at,
            r.hidden_reason,
            r.created_at,
            r.edited_at,
        )
        for r in Review.objects.select_related("user", "product", "hidden_by").order_by(
            "user__username", "product__slug"
        )
    ]
    restrictions = [
        (
            x.user.username,
            x.product.slug,
            x.hidden_reason,
            x.hidden_by.username if x.hidden_by else None,
            x.hidden_at,
            x.created_at,
        )
        for x in ReviewRestriction.objects.select_related(
            "user", "product", "hidden_by"
        ).order_by("user__username", "product__slug")
    ]
    return reviews, restrictions


@pytest.mark.usefixtures("frozen_clock")
def test_seeded_reviews_follow_a_valid_timeline_and_repeat_exactly(db):
    call_command("seed")
    now = FROZEN_NOW

    reviews = list(Review.objects.select_related("user", "product"))
    assert reviews, "there are reviews to check"
    for review in reviews:
        ordered = first_delivery(review.user, review.product)
        stamps = [review.created_at, review.edited_at, review.hidden_at]
        assert all(s is None or timezone.is_aware(s) for s in stamps), review
        # Posted after the order it reviews, and before the seed ran.
        assert ordered < review.created_at < now, review
        # Edits and hides come after posting, and before the seed ran.
        if review.edited_at:
            assert review.created_at < review.edited_at < now, review
        if review.hidden_at:
            assert review.created_at < review.hidden_at < now, review

    for restriction in ReviewRestriction.objects.select_related("user", "product"):
        ordered = first_delivery(restriction.user, restriction.product)
        assert timezone.is_aware(restriction.hidden_at)
        assert timezone.is_aware(restriction.created_at)
        # Hidden after the order, deleted (so restricted) after the hide.
        assert ordered < restriction.hidden_at < restriction.created_at < now

    # Run it again at the same clock: every review and restriction is
    # identical, timestamps included.
    first = review_data()
    call_command("seed")
    assert review_data() == first


# --- Wipe, counts and the success message (normal tests) ------------------------


def test_the_seed_wipes_every_review_and_restriction_first(
    other_customer, product, staff_user
):
    """Even ones by a user the seed doesn't manage, on a product it doesn't."""
    Review.objects.create(user=other_customer, product=product, rating=3)
    ReviewRestriction.objects.create(
        user=other_customer,
        product=product,
        hidden_reason="Spam",
        hidden_by=staff_user,
        hidden_at=timezone.now(),
    )

    call_command("seed")

    assert not Review.objects.filter(user=other_customer).exists()
    assert not ReviewRestriction.objects.filter(user=other_customer).exists()


@pytest.mark.usefixtures("frozen_clock")
def test_seeding_twice_leaves_the_same_review_counts(db):
    def counts():
        return (
            Review.objects.count(),
            Review.objects.filter(status=Review.Status.HIDDEN).count(),
            Review.objects.filter(edited_at__isnull=False).count(),
            ReviewRestriction.objects.count(),
        )

    call_command("seed")
    first = counts()
    call_command("seed")

    assert counts() == first


@pytest.mark.usefixtures("frozen_clock")
def test_the_success_message_reports_the_reviews(db):
    output = io.StringIO()

    call_command("seed", stdout=output)

    reviews = Review.objects.count()
    hidden = Review.objects.filter(status=Review.Status.HIDDEN).count()
    assert (
        f"{reviews} reviews ({hidden} hidden) and 1 review restriction."
        in output.getvalue()
    )
    assert "a 4-item wishlist" in output.getvalue()  # the rest is unchanged
