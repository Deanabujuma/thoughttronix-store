"""The Security overview page: who can reach it and what the Email card shows."""

from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

NO_EMAIL_NOTICE = (
    "No email address on file. Add an email address to enable password recovery."
)


@pytest.fixture
def dana(db):
    return User.objects.create_user(
        username="dana", email="dana@example.com", password="dana12345"
    )


@pytest.fixture
def superuser(db):
    """The administrator, with no email on file, like the seeded admin."""
    return User.objects.create_superuser(username="admin", password="admin123")


# --- Access -----------------------------------------------------------------


def test_security_redirects_signed_out_visitors_to_login(client, db):
    url = reverse("accounts:security")

    response = client.get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{reverse('accounts:login')}?next={url}"


@pytest.mark.parametrize("user_fixture", ["dana", "staff_user", "superuser"])
def test_every_role_gets_the_same_security_page(client, request, user_fixture):
    client.force_login(request.getfixturevalue(user_fixture))

    response = client.get(reverse("accounts:security"))

    assert response.status_code == HTTPStatus.OK
    assert [t.name for t in response.templates][0] == "accounts/security.html"


# --- Email card ---------------------------------------------------------------


def test_the_email_card_shows_the_address_on_file(client, dana):
    client.force_login(dana)

    response = client.get(reverse("accounts:security"))

    assert "dana@example.com" in response.content.decode()
    assert NO_EMAIL_NOTICE not in response.content.decode()


@pytest.mark.parametrize("user_fixture", ["customer", "staff_user", "superuser"])
def test_a_blank_email_shows_the_no_email_notice(client, request, user_fixture):
    client.force_login(request.getfixturevalue(user_fixture))

    response = client.get(reverse("accounts:security"))

    assert NO_EMAIL_NOTICE in response.content.decode()


# --- Navbar -------------------------------------------------------------------


def test_signed_in_users_see_the_security_link_after_addresses(client, customer):
    client.force_login(customer)

    html = client.get(reverse("products:catalog")).content.decode()

    addresses = html.index(f'href="{reverse("accounts:addresses")}"')
    security = html.index(f'href="{reverse("accounts:security")}"')
    assert addresses < security


def test_signed_out_visitors_do_not_see_the_security_link(client, db):
    html = client.get(reverse("products:catalog")).content.decode()

    assert f'href="{reverse("accounts:security")}"' not in html
