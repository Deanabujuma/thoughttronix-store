"""Password reset, confirm side: the new password, dead links, the notice."""

import email
import re
from datetime import datetime, timedelta
from email import policy
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from accounts.test_password_reset import link_in, request_reset, reset_link

User = get_user_model()

OLD_PASSWORD = "dana12345"
NEW_PASSWORD = "brand-new-thought-42"
SUCCESS_MESSAGE = (
    "Your password has been reset successfully. Please sign in with your new password."
)
NOTICE_TEMPLATE = "accounts/emails/password_changed_notice.txt"


@pytest.fixture
def dana(db):
    return User.objects.create_user(
        username="dana", email="dana@example.com", password=OLD_PASSWORD
    )


def uid_and_token(link):
    return link.rstrip("/").split("/")[-2:]


def set_password(client, link, password1=NEW_PASSWORD, password2=NEW_PASSWORD):
    """Open a reset link, then submit the form it leads to.

    A good link redirects to the form; a dead one doesn't, so the post goes
    back to the link itself.
    """
    chain = client.get(link, follow=True).redirect_chain
    form_url = chain[-1][0] if chain else link
    return client.post(
        form_url, {"new_password1": password1, "new_password2": password2}
    )


def is_invalid_link_page(response) -> bool:
    html = response.content.decode()
    return (
        "Invalid reset link" in html
        and f'href="{reverse("accounts:password_reset")}"' in html
        and 'name="new_password1"' not in html
    )


def token_clock(monkeypatch, seconds_later):
    """Make the token generator's clock read ``seconds_later`` from now."""
    later = datetime.now() + timedelta(seconds=seconds_later)
    monkeypatch.setattr(PasswordResetTokenGenerator, "_now", lambda self: later)


# --- The form -----------------------------------------------------------------


def test_the_emailed_link_opens_a_new_password_form(client, dana, mailoutbox):
    request_reset(client, "dana@example.com")

    response = client.get(link_in(mailoutbox[0]), follow=True)

    html = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert [t.name for t in response.templates][0] == (
        "accounts/password_reset_confirm.html"
    )
    assert "Choose a new password" in html
    assert 'name="new_password1"' in html
    assert 'name="new_password2"' in html
    assert 'class="input w-full"' in html
    assert "recognized" not in html  # no holding-page wording left


def test_the_token_is_kept_out_of_the_address_bar(client, dana):
    link = reset_link(dana)
    _, token = uid_and_token(link)

    response = client.get(link, follow=True)

    final_url = response.redirect_chain[-1][0]
    assert token not in final_url
    assert final_url.endswith("/set-password/")


@pytest.mark.parametrize(
    ("password1", "password2"),
    [
        ("short", "short"),  # too short
        ("12345678", "12345678"),  # common and entirely numeric
        ("dana@example.com", "dana@example.com"),  # too like the account
        (NEW_PASSWORD, "something-else-42"),  # mismatch
    ],
)
def test_a_rejected_password_changes_nothing_and_sends_nothing(
    client, dana, mailoutbox, password1, password2
):
    response = set_password(client, reset_link(dana), password1, password2)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors
    assert 'class="mt-1 text-sm text-error"' in response.content.decode()
    dana.refresh_from_db()
    assert dana.check_password(OLD_PASSWORD)
    assert mailoutbox == []


def test_a_rejected_password_leaves_the_link_usable(client, dana):
    link = reset_link(dana)
    set_password(client, link, "short", "short")

    response = set_password(client, link)

    assert response.url == reverse("accounts:login")


# --- Success ------------------------------------------------------------------


def test_a_reset_lands_on_login_with_the_message_without_signing_in(client, dana):
    response = set_password(client, reset_link(dana))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:login")
    assert "_auth_user_id" not in client.session

    login = client.get(response.url)
    assert SUCCESS_MESSAGE in login.content.decode()
    assert not login.wsgi_request.user.is_authenticated


def test_the_reset_complete_url_leads_on_to_login(client):
    response = client.get(reverse("accounts:password_reset_complete"))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:login")


def test_the_new_password_works_and_the_old_one_does_not(client, dana):
    set_password(client, reset_link(dana))

    assert not client.login(username="dana", password=OLD_PASSWORD)
    assert client.login(username="dana", password=NEW_PASSWORD)


def test_a_reset_signs_out_existing_sessions(client, dana):
    other_device = Client()
    other_device.force_login(dana)
    security = reverse("accounts:security")
    assert other_device.get(security).status_code == HTTPStatus.OK

    set_password(client, reset_link(dana))

    response = other_device.get(security)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))


# --- The link as delivered -------------------------------------------------
#
# A link at the dev server's host runs past 78 characters, so the email goes
# out quoted-printable and the console backend prints it with a soft line
# break: the raw text has an "=" and a newline inside the token. These tests
# read the link back the way a mail client does, from the encoded bytes.

DEV_HOST = "127.0.0.1:8000"


def delivered_link(message):
    """The reset link as a mail client shows it, decoded from the wire."""
    raw = message.message().as_bytes()
    body = email.message_from_bytes(raw, policy=policy.default).get_content()
    return re.search(r"https?://\S+", body).group()


def test_a_long_link_is_wrapped_on_the_wire(client, dana, mailoutbox):
    """Pins the cause of the console's "=" line breaks, so it stays explained."""
    client.post(
        reverse("accounts:password_reset"),
        {"email": "dana@example.com"},
        HTTP_HOST=DEV_HOST,
    )

    message = mailoutbox[0].message()
    link = link_in(mailoutbox[0])
    assert len(link) > 78
    assert message["Content-Transfer-Encoding"] == "quoted-printable"
    assert link not in message.as_bytes().decode()  # split by a soft break


def test_a_link_read_from_the_delivered_email_resets_the_password(
    client, dana, mailoutbox
):
    client.post(
        reverse("accounts:password_reset"),
        {"email": "dana@example.com"},
        HTTP_HOST=DEV_HOST,
    )
    link = delivered_link(mailoutbox[0])
    assert link == link_in(mailoutbox[0])
    assert link.startswith(f"http://{DEV_HOST}/")
    path = link.removeprefix(f"http://{DEV_HOST}")

    form = client.get(path, HTTP_HOST=DEV_HOST, follow=True)
    assert form.redirect_chain[0][1] == HTTPStatus.FOUND  # no 301 detour
    assert 'name="new_password1"' in form.content.decode()

    done = client.post(
        form.redirect_chain[-1][0],
        {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD},
        HTTP_HOST=DEV_HOST,
        follow=True,
    )

    assert done.redirect_chain[0][0] == reverse("accounts:login")
    assert SUCCESS_MESSAGE in done.content.decode()
    assert client.login(username="dana", password=NEW_PASSWORD)


# --- Dead links ---------------------------------------------------------------


def test_a_used_link_is_invalid(client, dana):
    link = reset_link(dana)
    set_password(client, link)

    assert is_invalid_link_page(client.get(link, follow=True))


def test_a_used_link_cannot_set_the_password_again(client, dana, mailoutbox):
    link = reset_link(dana)
    set_password(client, link)

    response = set_password(Client(), link, "another-thought-99", "another-thought-99")

    assert is_invalid_link_page(response)
    dana.refresh_from_db()
    assert dana.check_password(NEW_PASSWORD)
    assert len(mailoutbox) == 1  # the first reset's notice only


def test_a_link_still_works_just_before_the_timeout(
    client, dana, settings, monkeypatch
):
    settings.PASSWORD_RESET_TIMEOUT = 60
    link = reset_link(dana)
    token_clock(monkeypatch, 59)

    response = client.get(link, follow=True)

    assert 'name="new_password1"' in response.content.decode()


def test_a_link_past_the_timeout_is_invalid(client, dana, settings, monkeypatch):
    settings.PASSWORD_RESET_TIMEOUT = 60
    link = reset_link(dana)
    token_clock(monkeypatch, 61)

    assert is_invalid_link_page(client.get(link, follow=True))


def test_a_link_expires_after_one_hour_by_default(client, dana, monkeypatch):
    link = reset_link(dana)
    token_clock(monkeypatch, 60 * 60 + 1)

    assert is_invalid_link_page(client.get(link, follow=True))


def test_a_link_issued_before_a_later_password_change_is_invalid(client, dana):
    link = reset_link(dana)
    dana.set_password("changed-elsewhere-7")
    dana.save()

    assert is_invalid_link_page(client.get(link, follow=True))


def test_a_tampered_token_is_invalid(client, dana):
    uid, _ = uid_and_token(reset_link(dana))
    url = reverse("accounts:password_reset_confirm", args=[uid, "abc-123tampered"])

    assert is_invalid_link_page(client.get(url))


def test_an_unknown_uid_is_invalid_and_reveals_nothing(client, dana):
    _, token = uid_and_token(reset_link(dana))
    url = reverse("accounts:password_reset_confirm", args=["bm9wZQ", token])

    response = client.get(url)

    assert is_invalid_link_page(response)
    assert "dana" not in response.content.decode()


def test_a_post_without_a_checked_link_changes_nothing(client, dana, mailoutbox):
    """Skipping the emailed link and posting straight to the form fails."""
    uid, _ = uid_and_token(reset_link(dana))
    url = reverse("accounts:password_reset_confirm", args=[uid, "set-password"])

    response = client.post(
        url, {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD}
    )

    assert is_invalid_link_page(response)
    dana.refresh_from_db()
    assert dana.check_password(OLD_PASSWORD)
    assert mailoutbox == []


# --- The password-changed notice ---------------------------------------------


def test_a_reset_sends_one_password_changed_notice(client, dana, mailoutbox):
    response = set_password(client, reset_link(dana))

    assert len(mailoutbox) == 1
    notice = mailoutbox[0]
    assert notice.to == ["dana@example.com"]
    assert notice.subject == "Your ThoughtTronix password was changed"
    assert notice.content_subtype == "plain"
    assert notice.alternatives == []
    assert NOTICE_TEMPLATE in {t.name for t in response.templates}


def test_the_notice_has_the_date_and_a_reset_link_but_no_secrets(
    client, dana, mailoutbox
):
    link = reset_link(dana)
    uid, token = uid_and_token(link)

    set_password(client, link)

    body = mailoutbox[0].body
    assert datetime.now().strftime("%B") in body
    assert f"http://testserver{reverse('accounts:password_reset')}" in body
    for secret in (NEW_PASSWORD, OLD_PASSWORD, uid, token, "/reset/"):
        assert secret not in body


def test_the_notice_comes_from_the_configured_sender(
    client, dana, mailoutbox, settings
):
    settings.DEFAULT_FROM_EMAIL = "Store <store@example.com>"

    set_password(client, reset_link(dana))

    assert mailoutbox[0].from_email == "Store <store@example.com>"


def test_a_reset_for_a_user_without_an_email_sends_nothing(
    client, customer, mailoutbox
):
    """Staff can't request a link without an email, but nothing breaks."""
    response = set_password(client, reset_link(customer))

    assert response.url == reverse("accounts:login")
    assert mailoutbox == []


# --- send_security_notice -----------------------------------------------------


def test_a_notice_goes_nowhere_without_an_email(customer, mailoutbox):
    assert customer.send_security_notice("Subject", NOTICE_TEMPLATE) is False
    assert mailoutbox == []


def test_a_notice_defaults_to_the_current_email(dana, mailoutbox):
    assert dana.send_security_notice("Subject", NOTICE_TEMPLATE) is True
    assert mailoutbox[0].to == ["dana@example.com"]


def test_a_notice_can_go_to_an_explicit_recipient(customer, mailoutbox):
    sent = customer.send_security_notice(
        "Subject", NOTICE_TEMPLATE, recipient="old@example.com"
    )

    assert sent is True
    assert mailoutbox[0].to == ["old@example.com"]


# --- Changes outside the self-service flow stay silent -----------------------


def test_set_password_and_save_sends_nothing(dana, mailoutbox):
    dana.set_password("quiet-change-11")
    dana.save()

    assert mailoutbox == []


def test_an_admin_password_change_sends_nothing(admin_client, dana, mailoutbox):
    url = reverse("admin:auth_user_password_change", args=[dana.pk])

    response = admin_client.post(
        url, {"password1": "admin-chosen-77", "password2": "admin-chosen-77"}
    )

    assert response.status_code == HTTPStatus.FOUND
    dana.refresh_from_db()
    assert dana.check_password("admin-chosen-77")
    assert mailoutbox == []


def test_seed_sends_nothing(db, mailoutbox):
    call_command("seed")

    assert mailoutbox == []
