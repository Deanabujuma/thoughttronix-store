"""Sign out of all other devices: the salt, the form, and the sessions it ends."""

from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import escape
from django.utils.http import urlsafe_base64_encode

User = get_user_model()

PASSWORD = "dana12345"
SUCCESS_MESSAGE = "You've been signed out of all other devices."
WRONG_PASSWORD_ERROR = (
    "Your current password was entered incorrectly. Please enter it again."
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


def signed_in(user) -> Client:
    """A separate browser, signed in as ``user``."""
    device = Client()
    device.force_login(user)
    return device


def is_signed_in(device: Client) -> bool:
    """Whether ``device`` can still load the Security page."""
    return device.get(reverse("accounts:security")).status_code == HTTPStatus.OK


def sign_out_others(device: Client, password=PASSWORD, **extra):
    return device.post(
        reverse("accounts:sign_out_other_devices"),
        {"current_password": password},
        **extra,
    )


# --- The session salt ---------------------------------------------------------


def test_every_new_user_gets_their_own_salt(dana, customer, staff_user):
    salts = [u.session_salt for u in (dana, customer, staff_user)]

    assert all(salts)
    assert len(set(salts)) == len(salts)


def test_rotating_the_salt_changes_the_session_hash_but_not_the_password(dana):
    password_hash = dana.password
    session_hash = dana.get_session_auth_hash()
    old_salt = dana.session_salt

    dana.sign_out_other_sessions()

    dana.refresh_from_db()
    assert dana.session_salt != old_salt
    assert dana.get_session_auth_hash() != session_hash
    assert dana.password == password_hash


def test_the_session_hash_still_follows_the_password(dana):
    session_hash = dana.get_session_auth_hash()

    dana.set_password("brand-new-thought-42")

    assert dana.get_session_auth_hash() != session_hash


def test_salt_is_not_editable_in_the_admin(admin_client, dana):
    response = admin_client.get(reverse("admin:accounts_user_change", args=[dana.pk]))

    assert response.status_code == HTTPStatus.OK
    assert "session_salt" not in response.content.decode()


def test_seeded_users_have_distinct_salts_and_still_sign_in(db):
    call_command("seed")

    salts = list(User.objects.values_list("session_salt", flat=True))
    assert all(salts)
    assert len(set(salts)) == len(salts)
    assert Client().login(username="customer", password="customer123")


# --- The migration ------------------------------------------------------------

BEFORE = [("accounts", "0004_unique_lowercase_email")]
AFTER = [("accounts", "0005_user_session_salt")]


def _migrate(targets):
    """Migrate accounts to ``targets``; return that state's app registry."""
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


@pytest.mark.django_db(transaction=True)
def test_migration_gives_each_existing_user_a_distinct_salt():
    try:
        OldUser = _migrate(BEFORE).get_model("accounts", "User")
        for name in ("dana", "kai", "admin"):
            OldUser.objects.create(username=name, email=f"{name}@example.com")

        _migrate(AFTER)

        salts = list(User.objects.values_list("session_salt", flat=True))
        assert len(salts) == 3
        assert all(salts)
        assert len(set(salts)) == 3
    finally:
        _migrate(AFTER)


@pytest.mark.django_db(transaction=True)
def test_users_from_before_the_migration_still_sign_in():
    try:
        OldUser = _migrate(BEFORE).get_model("accounts", "User")
        # The historical model has no set_password; hash with the real one.
        OldUser.objects.create(username="dana", password=make_password(PASSWORD))

        _migrate(AFTER)

        device = Client()
        assert device.login(username="dana", password=PASSWORD)
        assert is_signed_in(device)
    finally:
        _migrate(AFTER)


# --- The Security page's Devices card -----------------------------------------


def test_the_security_page_has_a_devices_card(client, dana):
    client.force_login(dana)

    html = client.get(reverse("accounts:security")).content.decode()

    assert "Devices" in html
    assert f'href="{reverse("accounts:sign_out_other_devices")}"' in html
    assert "Sign out of all other devices" in html


# --- Access -------------------------------------------------------------------


def test_signed_out_visitors_are_sent_to_login(client, db):
    url = reverse("accounts:sign_out_other_devices")

    response = client.get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{reverse('accounts:login')}?next={url}"


def test_a_signed_out_post_signs_nobody_out(client, dana):
    other_device = signed_in(dana)
    salt = dana.session_salt

    response = sign_out_others(client)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))
    dana.refresh_from_db()
    assert dana.session_salt == salt
    assert is_signed_in(other_device)


@pytest.mark.parametrize("user_fixture", ["dana", "staff_user", "superuser"])
def test_every_role_gets_the_confirmation_form(client, request, user_fixture):
    client.force_login(request.getfixturevalue(user_fixture))

    response = client.get(reverse("accounts:sign_out_other_devices"))

    html = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert [t.name for t in response.templates][0] == (
        "accounts/sign_out_other_devices.html"
    )
    assert list(response.context["form"].fields) == ["current_password"]
    assert 'name="current_password"' in html
    assert 'type="password"' in html
    assert 'class="input w-full"' in html


@pytest.mark.parametrize(
    ("user_fixture", "password"),
    [("dana", PASSWORD), ("staff_user", "employee123"), ("superuser", "admin123")],
)
def test_every_role_can_sign_out_their_other_devices(request, user_fixture, password):
    user = request.getfixturevalue(user_fixture)
    this_device, other_device = signed_in(user), signed_in(user)

    response = sign_out_others(this_device, password)

    assert response.url == reverse("accounts:security")
    assert is_signed_in(this_device)
    assert not is_signed_in(other_device)


def test_viewing_the_form_signs_nobody_out(dana):
    this_device, other_device = signed_in(dana), signed_in(dana)

    this_device.get(reverse("accounts:sign_out_other_devices"))

    assert is_signed_in(other_device)


def test_the_post_requires_a_csrf_token(dana):
    this_device = Client(enforce_csrf_checks=True)
    this_device.force_login(dana)
    other_device = signed_in(dana)

    response = sign_out_others(this_device)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert is_signed_in(other_device)


# --- Rejected attempts --------------------------------------------------------


@pytest.mark.parametrize("password", ["wrong-password", "", "customer123"])
def test_a_wrong_password_shows_an_error_and_signs_nobody_out(
    customer, dana, mailoutbox, password
):
    """Includes another user's password: only the signed-in user's counts."""
    this_device, other_device = signed_in(dana), signed_in(dana)
    salt = dana.session_salt

    response = sign_out_others(this_device, password)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["current_password"]
    dana.refresh_from_db()
    assert dana.session_salt == salt
    assert is_signed_in(this_device)
    assert is_signed_in(other_device)
    assert mailoutbox == []


def test_a_wrong_password_says_so(dana):
    response = sign_out_others(signed_in(dana), "wrong-password")

    html = response.content.decode()
    assert WRONG_PASSWORD_ERROR in html
    assert 'class="mt-1 text-sm text-error"' in html


# --- Success ------------------------------------------------------------------


def test_success_returns_to_security_with_a_message(dana):
    response = sign_out_others(signed_in(dana), follow=True)

    assert response.redirect_chain == [(reverse("accounts:security"), HTTPStatus.FOUND)]
    assert escape(SUCCESS_MESSAGE) in response.content.decode()


def test_this_device_stays_signed_in_and_every_other_is_signed_out(dana):
    this_device = signed_in(dana)
    others = [signed_in(dana), signed_in(dana)]
    assert all(is_signed_in(device) for device in others)

    sign_out_others(this_device)

    assert is_signed_in(this_device)
    for device in others:
        response = device.get(reverse("accounts:security"))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url.startswith(reverse("accounts:login"))


def test_a_signed_out_device_can_sign_in_again(dana):
    this_device, other_device = signed_in(dana), signed_in(dana)

    sign_out_others(this_device)

    assert not is_signed_in(other_device)
    assert other_device.login(username="dana", password=PASSWORD)
    assert is_signed_in(other_device)


def test_this_device_gets_a_fresh_session_key(dana):
    this_device = signed_in(dana)
    old_key = this_device.session.session_key

    sign_out_others(this_device)

    assert this_device.session.session_key != old_key
    assert is_signed_in(this_device)


def test_other_users_sessions_are_untouched(dana, customer, staff_user):
    this_device = signed_in(dana)
    customer_device, staff_device = signed_in(customer), signed_in(staff_user)
    salts = {u.pk: u.session_salt for u in (customer, staff_user)}

    sign_out_others(this_device)

    assert is_signed_in(customer_device)
    assert is_signed_in(staff_device)
    for user in (customer, staff_user):
        user.refresh_from_db()
        assert user.session_salt == salts[user.pk]


def test_only_the_signed_in_user_is_affected(dana, customer):
    """There is no user in the URL or form: the view always uses request.user."""
    this_device, customer_device = signed_in(dana), signed_in(customer)

    sign_out_others(this_device, user=customer.pk, username="customer")

    assert is_signed_in(customer_device)


def test_the_password_and_email_are_unchanged_and_no_mail_is_sent(dana, mailoutbox):
    password_hash = dana.password

    sign_out_others(signed_in(dana))

    dana.refresh_from_db()
    assert dana.password == password_hash
    assert dana.check_password(PASSWORD)
    assert dana.email == "dana@example.com"
    assert mailoutbox == []


def test_a_reset_link_issued_before_still_works(client, dana):
    # Signed in first: a sign-in updates last_login, which any reset token
    # (Django's own rule) is built from.
    this_device = signed_in(dana)
    dana.refresh_from_db()
    uid = urlsafe_base64_encode(force_bytes(dana.pk))
    token = default_token_generator.make_token(dana)

    sign_out_others(this_device)

    dana.refresh_from_db()
    assert default_token_generator.check_token(dana, token)
    response = client.get(
        reverse("accounts:password_reset_confirm", args=[uid, token]), follow=True
    )
    assert 'name="new_password1"' in response.content.decode()


def test_signing_out_twice_keeps_this_device_signed_in(dana):
    this_device, other_device = signed_in(dana), signed_in(dana)

    sign_out_others(this_device)
    sign_out_others(this_device)

    assert is_signed_in(this_device)
    assert not is_signed_in(other_device)


def test_a_password_change_still_signs_out_other_devices(dana):
    """Phase 5's built-in mechanism keeps working alongside the salt."""
    this_device, other_device = signed_in(dana), signed_in(dana)

    this_device.post(
        reverse("accounts:password_change"),
        {
            "old_password": PASSWORD,
            "new_password1": "brand-new-thought-42",
            "new_password2": "brand-new-thought-42",
        },
    )

    assert is_signed_in(this_device)
    assert not is_signed_in(other_device)
