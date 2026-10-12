import secrets
from collections.abc import Iterator, Mapping
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models.functions import Lower
from django.template.loader import render_to_string
from django.utils.crypto import salted_hmac

from .validators import US_STATES, zip_validator


def new_session_salt() -> str:
    """A fresh random value for ``User.session_salt``."""
    return secrets.token_hex(16)


class User(AbstractUser):
    """The store's user model.

    Roles use Django's own vocabulary and nothing else: customers are
    plain users, employees are ``is_staff``, the admin is ``is_superuser``.

    Email stays optional on the model, so staff and admin accounts without
    one remain valid; signup is what requires it. A non-blank email is
    stored lowercase and belongs to one account only, in any capitalization.

    ``session_salt`` is mixed into the session auth hash, so rotating it
    signs out every session that hasn't been refreshed with the new hash —
    "Sign out of all other devices" — without touching the password.
    """

    # Nullable per the PRD: an absent job title is unknown, not empty.
    job_title = models.CharField(max_length=150, null=True, blank=True)  # noqa: DJ001
    session_salt = models.CharField(
        max_length=32, default=new_session_salt, editable=False
    )

    class Meta(AbstractUser.Meta):
        constraints = [
            # Blank emails are left out, so any number of accounts can
            # have none — the same conditional pattern as Address.
            models.UniqueConstraint(
                Lower("email"),
                condition=~models.Q(email=""),
                name="unique_lowercase_email",
                violation_error_message="A user with that email address already exists.",
            ),
        ]

    def save(self, *args, **kwargs):
        """Lowercase the email on every save — signup, admin, shell, seed."""
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def get_session_auth_hash(self) -> str:
        """Django's password-based session hash, with ``session_salt`` mixed in."""
        return self._salted_session_auth_hash()

    def get_session_auth_fallback_hash(self) -> Iterator[str]:
        """The same hash under each of ``SECRET_KEY_FALLBACKS``."""
        for fallback_secret in settings.SECRET_KEY_FALLBACKS:
            yield self._salted_session_auth_hash(secret=fallback_secret)

    def _salted_session_auth_hash(self, secret: str | None = None) -> str:
        key_salt = "accounts.User.get_session_auth_hash"
        return salted_hmac(
            key_salt,
            f"{self.password}:{self.session_salt}",
            secret=secret,
            algorithm="sha256",
        ).hexdigest()

    def sign_out_other_sessions(self) -> None:
        """Rotate ``session_salt`` so every existing session fails its hash check.

        That includes the caller's own session: the view must follow this
        with ``update_session_auth_hash`` to keep the current device signed
        in. The password is untouched, so outstanding reset links still work
        and no notice is sent.
        """
        self.session_salt = new_session_salt()
        self.save(update_fields=["session_salt"])

    def send_security_notice(
        self,
        subject: str,
        template_name: str,
        context: Mapping[str, Any] | None = None,
        recipient: str | None = None,
    ) -> bool:
        """Email a plain-text security notice; return whether one was sent.

        It goes to ``recipient`` when given, else to the current email, and
        nothing is sent when there is no address. Views call this only after
        a change succeeds — never saves or signals — so the admin, shell,
        and ``seed`` stay silent. The template gets ``user`` plus
        ``context``, and must never be handed a password or token.
        """
        address = recipient or self.email
        if not address:
            return False
        body = render_to_string(template_name, {"user": self, **(context or {})})
        send_mail(subject, body, None, [address])
        return True


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
