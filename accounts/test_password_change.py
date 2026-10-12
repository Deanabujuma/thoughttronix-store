"""Change password from the Security page: the form, the sessions, the notice."""

from datetime import datetime
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()

OLD_PASSWORD = "dana12345"
NEW_PASSWORD = "brand-new-thought-42"
SUCCESS_MESSAGE = "Your password has been changed."
NOTICE_TEMPLATE = "accounts/emails/password_changed_notice.txt"


@pytest.fixture
def dana(db):
    return User.objects.create_user(
        username="dana", email="dana@example.com", password=OLD_PASSWORD
    )


@pytest.fixture
def superuser(db):
    """The administrator, with no email on file, like the seeded admin."""
    return User.objects.create_superuser(username="admin", password="admin123")


def change_password(
    client,
    old_password=OLD_PASSWORD,
    new_password1=NEW_PASSWORD,
    new_password2=NEW_PASSWORD,
    **extra,
):
    return client.post(
        reverse("accounts:password_change"),
        {
            "old_password": old_password,
            "new_password1": new_password1,
            "new_password2": new_password2,
        },
        **extra,
    )


# --- The Security page's Password card ---------------------------------------


def test_the_security_page_links_to_change_password(client, dana):
    client.force_login(dana)

    html = client.get(reverse("accounts:security")).content.decode()

    assert "Password" in html
    assert f'href="{reverse("accounts:password_change")}"' in html
    assert "Change password" in html


# --- Access -------------------------------------------------------------------


def test_change_password_redirects_signed_out_visitors_to_login(client, db):
    url = reverse("accounts:password_change")

    response = client.get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{reverse('accounts:login')}?next={url}"


def test_a_signed_out_post_changes_nothing(client, dana, mailoutbox):
    response = change_password(client)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))
    dana.refresh_from_db()
    assert dana.check_password(OLD_PASSWORD)
    assert mailoutbox == []


@pytest.mark.parametrize("user_fixture", ["dana", "staff_user", "superuser"])
def test_every_role_gets_the_change_password_form(client, request, user_fixture):
    client.force_login(request.getfixturevalue(user_fixture))

    response = client.get(reverse("accounts:password_change"))

    html = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert [t.name for t in response.templates][0] == "accounts/password_change.html"
    for name in ("old_password", "new_password1", "new_password2"):
        assert f'name="{name}"' in html
    assert 'class="input w-full"' in html


@pytest.mark.parametrize(
    ("user_fixture", "password"),
    [("staff_user", "employee123"), ("superuser", "admin123")],
)
def test_staff_and_admin_can_change_their_password(
    client, request, user_fixture, password
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)

    response = change_password(client, old_password=password)

    assert response.url == reverse("accounts:security")
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)


def test_only_the_signed_in_users_password_changes(client, dana, customer):
    """There is no user in the URL or form: the view always uses request.user."""
    client.force_login(dana)

    change_password(client, user=customer.pk, username="customer")

    dana.refresh_from_db()
    customer.refresh_from_db()
    assert dana.check_password(NEW_PASSWORD)
    assert customer.check_password("customer123")


def test_another_users_current_password_does_not_authorize_a_change(
    client, dana, customer, mailoutbox
):
    client.force_login(dana)

    response = change_password(client, old_password="customer123")

    assert response.context["form"].errors["old_password"]
    dana.refresh_from_db()
    customer.refresh_from_db()
    assert dana.check_password(OLD_PASSWORD)
    assert customer.check_password("customer123")
    assert mailoutbox == []


# --- Rejected changes ---------------------------------------------------------


@pytest.mark.parametrize(
    ("old_password", "password1", "password2", "field"),
    [
        ("wrong-password", NEW_PASSWORD, NEW_PASSWORD, "old_password"),
        (OLD_PASSWORD, NEW_PASSWORD, "something-else-42", "new_password2"),
        (OLD_PASSWORD, "short", "short", "new_password2"),  # too short
        (OLD_PASSWORD, "12345678", "12345678", "new_password2"),  # common, numeric
        (OLD_PASSWORD, "dana@example.com", "dana@example.com", "new_password2"),
    ],
)
def test_a_rejected_change_shows_field_errors_and_changes_nothing(
    client, dana, mailoutbox, old_password, password1, password2, field
):
    client.force_login(dana)

    response = change_password(client, old_password, password1, password2)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors[field]
    assert 'class="mt-1 text-sm text-error"' in response.content.decode()
    dana.refresh_from_db()
    assert dana.check_password(OLD_PASSWORD)
    assert mailoutbox == []


def test_a_wrong_current_password_says_so(client, dana):
    client.force_login(dana)

    response = change_password(client, old_password="wrong-password")

    assert "Your old password was entered incorrectly" in response.content.decode()


# --- Success ------------------------------------------------------------------


def test_a_change_returns_to_security_with_a_message(client, dana):
    client.force_login(dana)

    response = change_password(client, follow=True)

    assert response.redirect_chain == [(reverse("accounts:security"), HTTPStatus.FOUND)]
    assert SUCCESS_MESSAGE in response.content.decode()


def test_the_new_password_works_and_the_old_one_does_not(client, dana):
    client.force_login(dana)

    change_password(client)

    dana.refresh_from_db()
    assert dana.check_password(NEW_PASSWORD)
    assert not Client().login(username="dana", password=OLD_PASSWORD)
    assert Client().login(username="dana", password=NEW_PASSWORD)


def test_a_change_keeps_this_session_and_signs_out_others(client, dana):
    other_device = Client()
    other_device.force_login(dana)
    client.force_login(dana)
    security = reverse("accounts:security")
    assert other_device.get(security).status_code == HTTPStatus.OK

    change_password(client)

    assert client.get(security).status_code == HTTPStatus.OK
    response = other_device.get(security)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))


# --- The password-changed notice ---------------------------------------------


def test_a_change_sends_one_password_changed_notice(client, dana, mailoutbox):
    client.force_login(dana)

    response = change_password(client)

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
    client.force_login(dana)

    change_password(client)

    body = mailoutbox[0].body
    assert datetime.now().strftime("%B") in body
    assert f"http://testserver{reverse('accounts:password_reset')}" in body
    for secret in (NEW_PASSWORD, OLD_PASSWORD, "/reset/"):
        assert secret not in body


def test_a_user_without_an_email_changes_their_password_and_gets_no_mail(
    client, customer, mailoutbox
):
    client.force_login(customer)

    response = change_password(client, old_password="customer123", follow=True)

    assert response.redirect_chain[-1][0] == reverse("accounts:security")
    assert SUCCESS_MESSAGE in response.content.decode()
    customer.refresh_from_db()
    assert customer.check_password(NEW_PASSWORD)
    assert mailoutbox == []
