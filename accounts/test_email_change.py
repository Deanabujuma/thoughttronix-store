"""Change email from the Security page: the form, the rules, the notice."""

from datetime import datetime
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.forms import ChangeEmailForm

User = get_user_model()

PASSWORD = "dana12345"
NEW_EMAIL = "dana.new@example.com"
NOTICE_SUBJECT = "Your ThoughtTronix email address was changed"
NOTICE_TEMPLATE = "accounts/emails/email_changed_notice.txt"
NO_EMAIL_NOTICE = (
    "No email address on file. Add an email address to enable password recovery."
)


@pytest.fixture
def dana(db):
    return User.objects.create_user(
        username="dana", email="dana@example.com", password=PASSWORD
    )


@pytest.fixture
def superuser(db):
    """The administrator, with no email on file, like the seeded admin."""
    return User.objects.create_superuser(username="admin", password="admin123")


def change_email(client, email=NEW_EMAIL, current_password=PASSWORD, **extra):
    return client.post(
        reverse("accounts:email_change"),
        {"email": email, "current_password": current_password},
        **extra,
    )


# --- The Security page's Email card -------------------------------------------


@pytest.mark.parametrize("user_fixture", ["dana", "customer"])
def test_the_email_card_links_to_change_email(client, request, user_fixture):
    """With an address on file or without one, the button is there."""
    client.force_login(request.getfixturevalue(user_fixture))

    html = client.get(reverse("accounts:security")).content.decode()

    assert f'href="{reverse("accounts:email_change")}"' in html
    assert "Change email" in html


# --- Access -------------------------------------------------------------------


def test_change_email_redirects_signed_out_visitors_to_login(client, db):
    url = reverse("accounts:email_change")

    response = client.get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{reverse('accounts:login')}?next={url}"


def test_a_signed_out_post_changes_nothing(client, dana, mailoutbox):
    response = change_email(client)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))
    dana.refresh_from_db()
    assert dana.email == "dana@example.com"
    assert mailoutbox == []


@pytest.mark.parametrize("user_fixture", ["dana", "staff_user", "superuser"])
def test_every_role_gets_the_change_email_form(client, request, user_fixture):
    client.force_login(request.getfixturevalue(user_fixture))

    response = client.get(reverse("accounts:email_change"))

    html = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert [t.name for t in response.templates][0] == "accounts/email_change.html"
    assert 'name="email"' in html
    assert 'name="current_password"' in html
    assert 'type="password"' in html
    assert 'class="input w-full"' in html


@pytest.mark.parametrize(
    ("user_fixture", "password"),
    [("staff_user", "employee123"), ("superuser", "admin123")],
)
def test_staff_and_admin_can_change_their_email(
    client, request, user_fixture, password
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)

    response = change_email(client, current_password=password)

    assert response.url == reverse("accounts:security")
    user.refresh_from_db()
    assert user.email == NEW_EMAIL


def test_only_the_signed_in_users_email_changes(client, dana, customer):
    """There is no user in the URL or form: the view always uses request.user."""
    client.force_login(dana)

    change_email(client, user=customer.pk, username="customer")

    dana.refresh_from_db()
    customer.refresh_from_db()
    assert dana.email == NEW_EMAIL
    assert customer.email == ""


def test_another_users_password_does_not_authorize_a_change(
    client, dana, customer, mailoutbox
):
    client.force_login(dana)

    response = change_email(client, current_password="customer123")

    assert response.context["form"].errors["current_password"]
    dana.refresh_from_db()
    assert dana.email == "dana@example.com"
    assert mailoutbox == []


# --- Rejected changes ---------------------------------------------------------


@pytest.mark.parametrize(
    ("email", "current_password", "field"),
    [
        (NEW_EMAIL, "wrong-password", "current_password"),
        (NEW_EMAIL, "", "current_password"),
        ("", PASSWORD, "email"),
        ("   ", PASSWORD, "email"),
        ("not-an-email", PASSWORD, "email"),
        ("taken@example.com", PASSWORD, "email"),
        ("Taken@Example.COM", PASSWORD, "email"),
    ],
)
def test_a_rejected_change_shows_field_errors_and_changes_nothing(
    client, dana, mailoutbox, email, current_password, field
):
    User.objects.create_user(
        username="taken", email="taken@example.com", password="taken12345"
    )
    client.force_login(dana)

    response = change_email(client, email, current_password)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors[field]
    assert 'class="mt-1 text-sm text-error"' in response.content.decode()
    dana.refresh_from_db()
    assert dana.email == "dana@example.com"
    assert mailoutbox == []


def test_a_wrong_current_password_says_so(client, dana):
    client.force_login(dana)

    response = change_email(client, current_password="wrong-password")

    assert "Your current password was entered incorrectly" in (
        response.content.decode()
    )


def test_a_taken_email_says_so(client, dana, staff_user):
    staff_user.email = "employee@example.com"
    staff_user.save()
    client.force_login(dana)

    response = change_email(client, email="EMPLOYEE@example.com")

    assert response.context["form"].errors["email"] == [
        "A user with that email address already exists."
    ]


def test_losing_a_race_for_an_address_is_a_form_error_not_a_crash(
    client, dana, monkeypatch, mailoutbox
):
    """Another account claims the address after the duplicate check passes.

    The database constraint rejects the save; the user sees the usual
    field error and keeps their old email.
    """
    check_for_duplicates = ChangeEmailForm.clean_email

    def check_then_lose_the_race(form):
        email = check_for_duplicates(form)
        User.objects.create_user(
            username="rival", email=email.upper(), password="rival12345"
        )
        return email

    monkeypatch.setattr(ChangeEmailForm, "clean_email", check_then_lose_the_race)
    client.force_login(dana)

    response = change_email(client)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["email"] == [
        "A user with that email address already exists."
    ]
    html = response.content.decode()
    assert "dana@example.com" in html  # the page still shows the old address
    assert "has been changed" not in html
    dana.refresh_from_db()
    assert dana.email == "dana@example.com"
    assert User.objects.get(username="rival").email == NEW_EMAIL
    assert mailoutbox == []
    assert client.get(reverse("accounts:security")).status_code == HTTPStatus.OK


# --- Success ------------------------------------------------------------------


def test_a_change_returns_to_security_with_a_message_and_the_new_address(client, dana):
    client.force_login(dana)

    response = change_email(client, follow=True)

    assert response.redirect_chain == [(reverse("accounts:security"), HTTPStatus.FOUND)]
    html = response.content.decode()
    assert f"Your email address has been changed to {NEW_EMAIL}." in html
    assert "dana@example.com" not in html
    dana.refresh_from_db()
    assert dana.email == NEW_EMAIL


def test_a_new_email_is_stored_lowercase(client, dana):
    client.force_login(dana)

    change_email(client, email="Dana.NEW@Example.com")

    dana.refresh_from_db()
    assert dana.email == NEW_EMAIL


def test_reentering_your_own_address_in_other_capitals_is_accepted(
    client, dana, mailoutbox
):
    client.force_login(dana)

    response = change_email(client, email="DANA@Example.com", follow=True)

    assert response.redirect_chain[-1][0] == reverse("accounts:security")
    assert "Your email address is unchanged." in response.content.decode()
    dana.refresh_from_db()
    assert dana.email == "dana@example.com"
    assert mailoutbox == []


def test_the_change_keeps_the_user_signed_in(client, dana):
    client.force_login(dana)

    change_email(client)

    assert client.get(reverse("accounts:security")).status_code == HTTPStatus.OK


# --- The email-changed notice --------------------------------------------------


def test_a_change_sends_one_notice_to_the_previous_address_only(
    client, dana, mailoutbox
):
    client.force_login(dana)

    response = change_email(client)

    assert len(mailoutbox) == 1
    notice = mailoutbox[0]
    assert notice.to == ["dana@example.com"]
    assert notice.cc == []
    assert notice.bcc == []
    assert notice.subject == NOTICE_SUBJECT
    assert notice.content_subtype == "plain"
    assert notice.alternatives == []
    assert NOTICE_TEMPLATE in {t.name for t in response.templates}


def test_the_notice_has_the_date_but_no_secrets(client, dana, mailoutbox):
    client.force_login(dana)

    change_email(client)

    body = mailoutbox[0].body
    assert "dana" in body
    assert datetime.now().strftime("%B") in body
    for secret in (PASSWORD, NEW_EMAIL, "/reset/"):
        assert secret not in body


def test_a_user_without_an_email_can_add_one_without_a_notice(
    client, customer, mailoutbox
):
    client.force_login(customer)
    assert NO_EMAIL_NOTICE in client.get(reverse("accounts:security")).content.decode()

    response = change_email(
        client, email="Casey@Example.com", current_password="customer123", follow=True
    )

    html = response.content.decode()
    assert response.redirect_chain[-1][0] == reverse("accounts:security")
    assert "Your email address has been changed to casey@example.com." in html
    assert NO_EMAIL_NOTICE not in html
    customer.refresh_from_db()
    assert customer.email == "casey@example.com"
    assert mailoutbox == []


def test_an_admin_email_edit_sends_nothing(admin_client, dana, mailoutbox):
    url = reverse("admin:accounts_user_change", args=[dana.pk])
    data = {
        "username": dana.username,
        "first_name": "",
        "last_name": "",
        "email": "Dana.Admin@Example.com",
        "is_active": "on",
        "date_joined_0": dana.date_joined.strftime("%Y-%m-%d"),
        "date_joined_1": dana.date_joined.strftime("%H:%M:%S"),
        "job_title": "",
        "addresses-TOTAL_FORMS": "0",
        "addresses-INITIAL_FORMS": "0",
        "addresses-MIN_NUM_FORMS": "0",
        "addresses-MAX_NUM_FORMS": "1000",
    }

    response = admin_client.post(url, data)

    assert response.status_code == HTTPStatus.FOUND
    dana.refresh_from_db()
    assert dana.email == "dana.admin@example.com"
    assert mailoutbox == []


# --- Password reset follows the new address -----------------------------------


def test_after_a_change_reset_mail_goes_to_the_new_address_only(
    client, dana, mailoutbox
):
    client.force_login(dana)
    change_email(client)
    client.logout()
    mailoutbox.clear()

    client.post(reverse("accounts:password_reset"), {"email": "dana@example.com"})
    assert mailoutbox == []

    client.post(reverse("accounts:password_reset"), {"email": NEW_EMAIL})
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [NEW_EMAIL]
