from collections.abc import Mapping
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction

from .validators import US_STATES, zip_validator


class User(AbstractUser):
    """The store's user model.

    Roles use Django's own vocabulary and nothing else: customers are
    plain users, employees are ``is_staff``, the admin is ``is_superuser``.
    """

    # Nullable per the PRD: an absent job title is unknown, not empty.
    job_title = models.CharField(max_length=150, null=True, blank=True)  # noqa: DJ001


# Address field → the suffix of its checkout field (``shipping_zip`` etc.).
CHECKOUT_FIELDS = {
    "name": "name",
    "street": "street",
    "line2": "line2",
    "city": "city",
    "state": "state",
    "zip_code": "zip",
}


class AddressManager(models.Manager):
    def save_from_checkout(
        self, user, checkout_data: Mapping[str, Any], prefix: str
    ) -> "Address":
        """Save the ``shipping`` or ``billing`` half of a checkout.

        An exact copy of an address the user already has is not saved
        twice — the existing one is returned instead.
        """
        fields = {
            field: checkout_data[f"{prefix}_{suffix}"]
            for field, suffix in CHECKOUT_FIELDS.items()
        }
        existing = self.filter(user=user, **fields).first()
        return existing or self.create(user=user, **fields)


class Address(models.Model):
    """A saved address in a customer's address book.

    One address serves either purpose; the two defaults say which one
    checkout fills in for shipping and for billing. Orders copy addresses
    rather than pointing at them, so editing or deleting one never
    changes a past order.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(
        max_length=50, blank=True, help_text="Optional — e.g. Home or Work."
    )
    name = models.CharField("Full name", max_length=100)
    street = models.CharField("Street address", max_length=200)
    line2 = models.CharField("Apt, suite, etc. (optional)", max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, choices=US_STATES)
    zip_code = models.CharField("ZIP code", max_length=10, validators=[zip_validator])
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)

    objects = AddressManager()

    class Meta:
        ordering = ["pk"]
        verbose_name_plural = "addresses"
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default_shipping=True),
                name="one_default_shipping_per_user",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default_billing=True),
                name="one_default_billing_per_user",
            ),
        ]

    def __str__(self):
        return self.label or f"{self.street}, {self.city} {self.state}"

    def save(self, *args, **kwargs):
        """A new address fills whichever default the user doesn't have yet,
        so a customer's first address becomes both."""
        if self._state.adding:
            others = Address.objects.filter(user_id=self.user_id)
            if not others.filter(is_default_shipping=True).exists():
                self.is_default_shipping = True
            if not others.filter(is_default_billing=True).exists():
                self.is_default_billing = True
        super().save(*args, **kwargs)

    def make_default_shipping(self):
        self._make_default("is_default_shipping")

    def make_default_billing(self):
        self._make_default("is_default_billing")

    @transaction.atomic
    def _make_default(self, flag):
        # Clear the old default first, or the unique constraint rejects
        # the moment two defaults would briefly coexist.
        self.user.addresses.exclude(pk=self.pk).filter(**{flag: True}).update(
            **{flag: False}
        )
        setattr(self, flag, True)
        self.save(update_fields=[flag])

    def as_checkout_initial(self, prefix: str) -> dict[str, str]:
        """This address as ``CheckoutForm`` initial data for one section."""
        return {
            f"{prefix}_{suffix}": getattr(self, field)
            for field, suffix in CHECKOUT_FIELDS.items()
        }
