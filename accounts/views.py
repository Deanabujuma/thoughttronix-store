from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.humanize.templatetags.humanize import apnumber
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.template.defaultfilters import pluralize
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)

from .forms import (
    AddressForm,
    ChangeEmailForm,
    ChangePasswordForm,
    NewPasswordForm,
    PasswordResetRequestForm,
    SignInForm,
    SignOutOtherDevicesForm,
    SignupForm,
)
from .models import Address, User


class SignupView(SuccessMessageMixin, CreateView):
    """Create a customer account, then hand off to the login page.

    New users sign in themselves — auto-login after signup is left as a
    student exercise.
    """

    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:login")
    success_message = "Account created — you can now sign in."


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = SignInForm


class SignOutView(LogoutView):
    def post(self, request, *args, **kwargs):
        # Flash after super() has flushed the session, or the message
        # would be wiped along with it.
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have signed out.")
        return response


# --- Account security -------------------------------------------------------


class SecurityView(LoginRequiredMixin, TemplateView):
    """The Security overview: one page for every signed-in user, any role."""

    template_name = "accounts/security.html"


class ChangeEmailView(LoginRequiredMixin, FormView):
    """Change the signed-in user's own email, then tell the old address.

    The form is built for ``request.user`` and nobody else. The notice
    goes to the previous address only, so a takeover that redirects the
    account's email is seen by the real owner; there is none when the
    user had no address before or kept the same one.
    """

    form_class = ChangeEmailForm
    template_name = "accounts/email_change.html"
    success_url = reverse_lazy("accounts:security")

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def form_valid(self, form):
        user = self.request.user
        previous_email = user.email
        if not form.save():
            return self.form_invalid(form)
        if user.email == previous_email:
            messages.success(self.request, "Your email address is unchanged.")
            return super().form_valid(form)
        messages.success(
            self.request, f"Your email address has been changed to {user.email}."
        )
        # Checked here: a blank recipient would fall back to the new address.
        if previous_email:
            user.send_security_notice(
                "Your ThoughtTronix email address was changed",
                "accounts/emails/email_changed_notice.txt",
                {"changed_at": timezone.localtime()},
                recipient=previous_email,
            )
        return super().form_valid(form)


class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    """Change the signed-in user's own password, then send the notice.

    Django's view checks the current password, saves the new one, and
    calls ``update_session_auth_hash`` so this session survives. Every
    other session was signed in under the old password hash, so it fails
    Django's hash check on its next request.
    """

    form_class = ChangePasswordForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:security")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your password has been changed.")
        send_password_changed_notice(self.request, form.user)
        return response


class SignOutOtherDevicesView(LoginRequiredMixin, FormView):
    """Sign the user out everywhere but here, once they confirm their password.

    GET only shows the confirmation form; the sign-out is a POST. Rotating
    ``session_salt`` changes the session auth hash, so every session fails
    Django's hash check on its next request; ``update_session_auth_hash``
    then stores the new hash in this one, so it survives. The password is
    unchanged, so no notice is sent.
    """

    form_class = SignOutOtherDevicesForm
    template_name = "accounts/sign_out_other_devices.html"
    success_url = reverse_lazy("accounts:security")

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def form_valid(self, form):
        form.user.sign_out_other_sessions()
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, "You've been signed out of all other devices.")
        return super().form_valid(form)


# --- Password reset ---------------------------------------------------------


def reset_link_lifetime() -> str:
    """``PASSWORD_RESET_TIMEOUT`` in words, e.g. 3600 → "one hour"."""
    seconds = settings.PASSWORD_RESET_TIMEOUT
    for size, unit in ((3600, "hour"), (60, "minute"), (1, "second")):
        if seconds % size == 0:
            count = seconds // size
            return f"{apnumber(count)} {unit}{pluralize(count)}"


class PasswordResetRequestView(PasswordResetView):
    """Email a reset link; the next page is the same whatever was entered."""

    form_class = PasswordResetRequestForm
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/emails/password_reset_email.txt"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")

    def form_valid(self, form):
        self.extra_email_context = {"link_lifetime": reset_link_lifetime()}
        return super().form_valid(form)


class PasswordResetSentView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetSetView(PasswordResetConfirmView):
    """Choose a new password from an emailed link, then send the notice.

    Django checks the link, hides the token from the address bar, and
    uses it up: setting the password changes the hash the token is built
    from, which also signs out every existing session. The user is not
    signed in afterwards; they land on the login page to try the new
    password.
    """

    form_class = NewPasswordForm
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:login")
    post_reset_login = False

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Your password has been reset successfully. "
            "Please sign in with your new password.",
        )
        send_password_changed_notice(self.request, form.user)
        return response


class PasswordResetFinishedView(RedirectView):
    """Django's reset-complete stop, kept only as a way on to sign in."""

    pattern_name = "accounts:login"


def send_password_changed_notice(request, user: User) -> bool:
    """Tell ``user`` their password just changed, with a way back in."""
    return user.send_security_notice(
        "Your ThoughtTronix password was changed",
        "accounts/emails/password_changed_notice.txt",
        {
            "changed_at": timezone.localtime(),
            "reset_url": request.build_absolute_uri(reverse("accounts:password_reset")),
        },
    )


# --- Address book -----------------------------------------------------------


class OwnAddressMixin(LoginRequiredMixin):
    """Scope every lookup to the signed-in user's own addresses.

    Another customer's pk is simply not in the queryset, so it 404s.
    """

    success_url = reverse_lazy("accounts:addresses")

    def get_queryset(self):
        return self.request.user.addresses.all()


class AddressListView(OwnAddressMixin, ListView):
    template_name = "accounts/address_list.html"
    context_object_name = "addresses"


class AddressCreateView(OwnAddressMixin, SuccessMessageMixin, CreateView):
    form_class = AddressForm
    template_name = "accounts/address_form.html"
    success_message = "Address saved."

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AddressUpdateView(OwnAddressMixin, SuccessMessageMixin, UpdateView):
    form_class = AddressForm
    template_name = "accounts/address_form.html"
    success_message = "Address saved."


class AddressDeleteView(OwnAddressMixin, SuccessMessageMixin, DeleteView):
    template_name = "accounts/address_confirm_delete.html"
    context_object_name = "address"
    success_message = "Address deleted."


class MakeDefaultAddressView(LoginRequiredMixin, View):
    """POST-only: make one of the user's addresses a default, then go back."""

    kind = None  # "shipping" or "billing", set in the URLconf

    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        getattr(address, f"make_default_{self.kind}")()
        messages.success(request, f"{address} is now your default {self.kind} address.")
        return redirect("accounts:addresses")
