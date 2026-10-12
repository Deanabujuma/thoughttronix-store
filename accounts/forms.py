from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.db import IntegrityError, transaction

from .models import Address, User


class SignupForm(UserCreationForm):
    """Django's stock signup fields plus a required email.

    Username, email, password, confirmation — in that order. Email is how
    an account is recovered, so it must be unique in any capitalization.
    The widgets carry DaisyUI classes because plain Django forms own their
    own styling here.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"

    def clean_email(self) -> str:
        """Lowercase the email and reject one another account already uses."""
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "A user with that email address already exists.",
                code="duplicate_email",
            )
        return email


class SignInForm(AuthenticationForm):
    """The stock authentication form, dressed in DaisyUI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"


class PasswordResetRequestForm(PasswordResetForm):
    """Django's reset-request form, dressed in DaisyUI.

    The stock form already matches the email case-insensitively and skips
    inactive accounts and accounts without a usable password — quietly, so
    the page answers the same whatever was entered.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["class"] = "input w-full"


class NewPasswordForm(SetPasswordForm):
    """Django's set-password form, dressed in DaisyUI.

    The stock form checks the two entries match and runs the new password
    through ``AUTH_PASSWORD_VALIDATORS``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"


class ChangePasswordForm(PasswordChangeForm):
    """Django's password-change form, dressed in DaisyUI.

    The stock form checks the current password, checks the two new entries
    match, and runs the new password through ``AUTH_PASSWORD_VALIDATORS``.
    It only ever changes the password of the user it was built for — the
    view hands it ``request.user``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"


class ChangeEmailForm(forms.Form):
    """Change the signed-in user's email, authorized by their current password.

    The new email follows the signup rules: required, lowercased, and
    unique in any capitalization — the user's own account aside, so
    re-entering their address in other capitals is fine. Like Django's
    password forms, it is built for one user and only ever saves that one.
    """

    email = forms.EmailField(
        label="New email address",
        max_length=User._meta.get_field("email").max_length,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    current_password = forms.CharField(
        label="Current password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, user: User, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"

    @staticmethod
    def duplicate_email_error() -> forms.ValidationError:
        return forms.ValidationError(
            "A user with that email address already exists.", code="duplicate_email"
        )

    def clean_email(self) -> str:
        """Lowercase the email and reject one another account already uses."""
        email = self.cleaned_data["email"].lower()
        others = User.objects.exclude(pk=self.user.pk)
        if others.filter(email__iexact=email).exists():
            raise self.duplicate_email_error()
        return email

    def clean_current_password(self) -> str:
        password = self.cleaned_data["current_password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(
                "Your current password was entered incorrectly. Please enter it again.",
                code="password_incorrect",
            )
        return password

    def save(self) -> bool:
        """Save the new email; return whether it was saved.

        Another account can claim the same address between ``clean_email``
        and this save. The ``unique_lowercase_email`` constraint still
        rejects it, so that race ends as the usual field error on a valid
        form turned invalid, with the user's email left as it was.
        """
        previous_email = self.user.email
        self.user.email = self.cleaned_data["email"]
        try:
            # A savepoint, so the failed UPDATE doesn't break the request's
            # transaction for whatever runs after it.
            with transaction.atomic():
                self.user.save(update_fields=["email"])
        except IntegrityError:
            self.user.email = previous_email
            self.add_error("email", self.duplicate_email_error())
            return False
        return True


class AddressForm(forms.ModelForm):
    """Add or edit a saved address; the model's fields carry every rule.

    The defaults are left out — they change through their own buttons on
    the address book, never by editing an address.
    """

    class Meta:
        model = Address
        fields = ["label", "name", "street", "line2", "city", "state", "zip_code"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "select w-full"
            else:
                field.widget.attrs["class"] = "input w-full"
