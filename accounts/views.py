from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.humanize.templatetags.humanize import apnumber
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.template.defaultfilters import pluralize
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import AddressForm, PasswordResetRequestForm, SignInForm, SignupForm
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


@method_decorator(never_cache, name="dispatch")
class PasswordResetHoldingView(TemplateView):
    """A stand-in for the reset-confirm page until setting a password exists.

    It only checks the link: GET-only with no form, so no password can
    change here, and checking a token never uses it up.
    """

    template_name = "accounts/password_reset_holding.html"

    def get(self, request, uidb64, token):
        validlink = self.link_is_valid(uidb64, token)
        return self.render_to_response(self.get_context_data(validlink=validlink))

    @staticmethod
    def link_is_valid(uidb64: str, token: str) -> bool:
        """Whether the uid names a real user and the token is still good."""
        try:
            pk = urlsafe_base64_decode(uidb64).decode()
            user = User._default_manager.get(pk=pk)
        except (
            TypeError,
            ValueError,
            OverflowError,
            ValidationError,
            User.DoesNotExist,
        ):
            return False
        return default_token_generator.check_token(user, token)


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
