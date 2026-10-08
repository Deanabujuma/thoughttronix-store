"""Email identity: signup asks for an email, stored lowercase and unique."""

from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import reverse

User = get_user_model()

SIGNUP = {
    "username": "dana",
    "email": "Dana@Example.com",
    "password1": "neural-implant-9000",
    "password2": "neural-implant-9000",
}


@pytest.fixture
def dana(db):
    return User.objects.create_user(
        username="dana", email="dana@example.com", password="dana12345"
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(username="admin", password="admin123")


# --- Signup -----------------------------------------------------------------


def test_signup_asks_for_username_email_then_passwords(client, db):
    form = client.get(reverse("accounts:signup")).context["form"]

    assert list(form.fields) == ["username", "email", "password1", "password2"]
    assert form.fields["email"].required


def test_signup_stores_the_email_lowercase(client, db):
    client.post(reverse("accounts:signup"), SIGNUP)

    assert User.objects.get(username="dana").email == "dana@example.com"


def test_signup_requires_an_email(client, db):
    response = client.post(reverse("accounts:signup"), {**SIGNUP, "email": ""})

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["email"]
    assert not User.objects.filter(username="dana").exists()


@pytest.mark.parametrize("email", ["dana@example.com", "DANA@EXAMPLE.COM"])
def test_signup_rejects_an_email_in_use_in_any_capitalization(client, dana, email):
    response = client.post(
        reverse("accounts:signup"),
        {**SIGNUP, "username": "dana-two", "email": email},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["email"] == [
        "A user with that email address already exists."
    ]
    assert not User.objects.filter(username="dana-two").exists()


def test_new_customer_signs_in_with_username(client, db):
    client.post(reverse("accounts:signup"), SIGNUP)

    response = client.post(
        reverse("accounts:login"),
        {"username": "dana", "password": "neural-implant-9000"},
        follow=True,
    )

    assert response.context["user"].username == "dana"


# --- Model and database --------------------------------------------------------


def test_create_user_stores_the_email_lowercase(db):
    user = User.objects.create_user(username="dana", email="DANA@Example.COM")

    user.refresh_from_db()
    assert user.email == "dana@example.com"


def test_database_rejects_emails_differing_only_in_case(dana):
    # bulk_create skips save(), so the mixed case reaches the database
    # and only the constraint stands in the way.
    with pytest.raises(IntegrityError):
        User.objects.bulk_create([User(username="dana-two", email="DANA@example.com")])


def test_database_allows_many_blank_emails(db):
    User.objects.bulk_create(
        [User(username="first", email=""), User(username="second", email="")]
    )

    assert User.objects.filter(email="").count() == 2


def test_staff_without_email_still_signs_in(client, staff_user):
    assert staff_user.email == ""

    response = client.post(
        reverse("accounts:login"),
        {"username": "employee", "password": "employee123"},
        follow=True,
    )

    assert response.context["user"] == staff_user


# --- Django admin ------------------------------------------------------------


def _admin_change(user, **changes):
    """The POST body of the admin's user change form, as it stands."""
    return {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": "on",
        "date_joined_0": user.date_joined.strftime("%Y-%m-%d"),
        "date_joined_1": user.date_joined.strftime("%H:%M:%S"),
        "job_title": "",
        "addresses-TOTAL_FORMS": "0",
        "addresses-INITIAL_FORMS": "0",
        "addresses-MIN_NUM_FORMS": "0",
        "addresses-MAX_NUM_FORMS": "1000",
        **changes,
    }


def test_admin_stores_the_email_lowercase(client, admin_user, customer):
    client.force_login(admin_user)

    response = client.post(
        reverse("admin:accounts_user_change", args=[customer.pk]),
        _admin_change(customer, email="Casey@Example.COM"),
    )

    assert response.status_code == HTTPStatus.FOUND
    customer.refresh_from_db()
    assert customer.email == "casey@example.com"


def test_admin_rejects_a_duplicate_email(client, admin_user, customer, dana):
    client.force_login(admin_user)

    response = client.post(
        reverse("admin:accounts_user_change", args=[customer.pk]),
        _admin_change(customer, email="DANA@example.com"),
    )

    assert response.status_code == HTTPStatus.OK
    assert "A user with that email address already exists." in (
        response.content.decode()
    )
    customer.refresh_from_db()
    assert customer.email == ""


# --- Seed --------------------------------------------------------------------


def test_seed_gives_every_user_a_unique_lowercase_email(db):
    call_command("seed")

    emails = list(User.objects.values_list("email", flat=True))
    assert all(email and email == email.lower() for email in emails)
    assert len(set(emails)) == len(emails)


# --- Data migration ------------------------------------------------------------

BEFORE = [("accounts", "0002_address")]
AFTER = [("accounts", "0004_unique_lowercase_email")]


def _migrate(targets):
    """Migrate accounts to ``targets``; return that state's app registry."""
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


def _has_email_constraint() -> bool:
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, "accounts_user")
    return "unique_lowercase_email" in constraints


@pytest.mark.django_db(transaction=True)
def test_migration_lowercases_existing_emails():
    try:
        OldUser = _migrate(BEFORE).get_model("accounts", "User")
        OldUser.objects.create(username="dana", email="Dana@Example.COM")
        OldUser.objects.create(username="snoop", email="")

        _migrate(AFTER)

        assert User.objects.get(username="dana").email == "dana@example.com"
        assert User.objects.get(username="snoop").email == ""
        assert _has_email_constraint()
    finally:
        _migrate(AFTER)


@pytest.mark.django_db(transaction=True)
def test_migration_stops_on_duplicates_and_names_them():
    try:
        OldUser = _migrate(BEFORE).get_model("accounts", "User")
        OldUser.objects.create(username="dana", email="dana@example.com")
        OldUser.objects.create(username="dana-two", email="DANA@example.com")
        OldUser.objects.create(username="lone", email="Lone@example.com")

        with pytest.raises(RuntimeError) as error:
            _migrate(AFTER)

        assert "dana@example.com: dana, dana-two" in str(error.value)
        assert "lone" not in str(error.value)
        assert not _has_email_constraint()
    finally:
        # Clear the duplicates so the database can return to the latest state.
        OldUser.objects.all().delete()
        _migrate(AFTER)
