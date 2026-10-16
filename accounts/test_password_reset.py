"""Password reset, request side: the link, the generic answer, the email.

The page the emailed link opens is tested in ``test_password_reset_confirm``.
"""

import importlib
import re
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail.backends import console
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.module_loading import import_string
from environs import env

import config.settings

User = get_user_model()

SENT_MESSAGE = (
    "If an account exists with that email address, we've sent password-reset "
    "instructions. Please check your inbox and spam folder."
)


@pytest.fixture
def dana(db):
    return User.objects.create_user(
        username="dana", email="dana@example.com", password="dana12345"
    )


def request_reset(client, email):
    return client.post(reverse("accounts:password_reset"), {"email": email})


def reset_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return reverse("accounts:password_reset_confirm", args=[uid, token])


def page(response):
    """The page's HTML minus the CSRF token, which is re-masked every render."""
    return re.sub(r'"X-CSRFToken": "\w+"', "", response.content.decode())


def link_in(message):
    return re.search(r"https?://\S+", message.body).group()


# --- Login page ---------------------------------------------------------------


def test_the_login_page_links_to_forgot_password(client, db):
    html = client.get(reverse("accounts:login")).content.decode()

    assert f'href="{reverse("accounts:password_reset")}"' in html
    assert "Forgot password?" in html


# --- Request ------------------------------------------------------------------


def test_the_request_page_renders_for_signed_out_visitors(client, db):
    response = client.get(reverse("accounts:password_reset"))

    assert response.status_code == HTTPStatus.OK
    assert [t.name for t in response.templates][0] == (
        "accounts/password_reset_form.html"
    )


def test_a_request_redirects_to_the_generic_sent_page(client, dana):
    response = request_reset(client, "dana@example.com")

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:password_reset_done")
    assert SENT_MESSAGE in client.get(response.url).content.decode()


@pytest.mark.parametrize(
    "email",
    [
        "dana@example.com",  # registered
        "nobody@example.com",  # unregistered
        "DANA@Example.COM",  # registered, other capitalization
    ],
)
def test_the_answer_is_identical_whatever_was_entered(client, dana, customer, email):
    """The email-less ``customer`` exists too; nothing can reveal it either."""
    response = request_reset(client, email)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:password_reset_done")
    baseline = page(client.get(reverse("accounts:password_reset_done")))
    assert page(client.get(response.url)) == baseline


def test_an_account_without_an_email_gets_nothing(client, customer, mailoutbox):
    response = request_reset(client, "customer@example.com")

    assert response.url == reverse("accounts:password_reset_done")
    assert mailoutbox == []


@pytest.mark.parametrize("email", ["dana@example.com", "DANA@Example.COM"])
def test_a_registered_active_account_gets_exactly_one_email(
    client, dana, mailoutbox, email
):
    request_reset(client, email)

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["dana@example.com"]


def test_an_unregistered_email_gets_nothing(client, dana, mailoutbox):
    request_reset(client, "nobody@example.com")

    assert mailoutbox == []


def test_an_inactive_account_gets_nothing(client, dana, mailoutbox):
    dana.is_active = False
    dana.save()

    response = request_reset(client, "dana@example.com")

    assert response.url == reverse("accounts:password_reset_done")
    assert mailoutbox == []


def test_an_account_without_a_usable_password_gets_nothing(client, dana, mailoutbox):
    dana.set_unusable_password()
    dana.save()

    response = request_reset(client, "dana@example.com")

    assert response.url == reverse("accounts:password_reset_done")
    assert mailoutbox == []


# --- The email ----------------------------------------------------------------


def test_the_email_is_plain_text_from_the_configured_sender(
    client, dana, mailoutbox, settings
):
    settings.DEFAULT_FROM_EMAIL = "Store <store@example.com>"

    request_reset(client, "dana@example.com")

    message = mailoutbox[0]
    assert message.from_email == "Store <store@example.com>"
    assert message.content_subtype == "plain"
    assert message.alternatives == []
    assert message.subject == "Reset your ThoughtTronix password"


def test_the_email_says_the_link_expires_in_one_hour(client, dana, mailoutbox):
    request_reset(client, "dana@example.com")

    assert "expires in one hour" in mailoutbox[0].body


def test_the_expiry_wording_follows_the_configured_timeout(
    client, dana, mailoutbox, settings
):
    settings.PASSWORD_RESET_TIMEOUT = 1800

    request_reset(client, "dana@example.com")

    assert "expires in 30 minutes" in mailoutbox[0].body


def test_the_email_links_to_the_reset_confirm_page(client, dana, mailoutbox):
    request_reset(client, "dana@example.com")

    link = link_in(mailoutbox[0])
    assert link == f"http://testserver{reset_link(dana)}"


def test_the_email_templates_live_in_the_emails_folder(client, dana):
    response = request_reset(client, "dana@example.com")

    names = {t.name for t in response.templates}
    assert "accounts/emails/password_reset_email.txt" in names
    assert "accounts/emails/password_reset_subject.txt" in names


# --- Settings -----------------------------------------------------------------


@pytest.fixture
def reload_settings(monkeypatch):
    """Re-read config/settings.py without any .env file, then restore it."""
    monkeypatch.setattr(env, "read_env", lambda *args, **kwargs: None)
    yield lambda: importlib.reload(config.settings)
    monkeypatch.undo()
    importlib.reload(config.settings)


def test_the_settings_fall_back_to_their_defaults(monkeypatch, reload_settings):
    monkeypatch.delenv("PASSWORD_RESET_TIMEOUT", raising=False)
    monkeypatch.delenv("DEFAULT_FROM_EMAIL", raising=False)

    module = reload_settings()

    assert module.PASSWORD_RESET_TIMEOUT == 3600
    assert module.DEFAULT_FROM_EMAIL == "ThoughtTronix <no-reply@thoughttronix.example>"


def test_the_settings_read_the_environment(monkeypatch, reload_settings):
    monkeypatch.setenv("PASSWORD_RESET_TIMEOUT", "900")
    monkeypatch.setenv("DEFAULT_FROM_EMAIL", "Ops <ops@example.com>")

    module = reload_settings()

    assert module.PASSWORD_RESET_TIMEOUT == 900
    assert module.DEFAULT_FROM_EMAIL == "Ops <ops@example.com>"


def test_email_still_goes_to_the_console(reload_settings):
    # pytest-django swaps in locmem for tests, so read the settings module.
    module = reload_settings()

    backend = import_string(module.EMAIL_BACKEND)
    assert issubclass(backend, console.EmailBackend)
