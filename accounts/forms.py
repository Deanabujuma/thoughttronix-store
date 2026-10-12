from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

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
