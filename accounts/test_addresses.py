"""Saved addresses: the model's default rules and the address book pages."""

from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse

from .models import Address

WORK = {
    "label": "Work",
    "name": "Casey Monroe",
    "street": "1 Neural Plaza",
    "line2": "Floor 12",
    "city": "Amarillo",
    "state": "TX",
    "zip_code": "79101",
}


@pytest.fixture
def work(customer, address):
    return Address.objects.create(user=customer, **WORK)


@pytest.fixture
def other_customer(db):
    return get_user_model().objects.create_user(username="other", password="x")


# --- Model behavior ----------------------------------------------------------


def test_str_is_the_label_or_falls_back_to_the_address(address):
    assert str(address) == "Home"

    address.label = ""
    assert str(address) == "214 Synapse Street, Canyon TX"


def test_the_first_address_becomes_both_defaults(address):
    assert address.is_default_shipping
    assert address.is_default_billing


def test_later_addresses_are_not_defaults(work):
    assert not work.is_default_shipping
    assert not work.is_default_billing


def test_a_new_address_fills_a_missing_default(customer, address):
    address.is_default_billing = False
    address.save()

    work = Address.objects.create(user=customer, **WORK)

    assert not work.is_default_shipping
    assert work.is_default_billing


def test_the_database_rejects_two_default_shipping_addresses(address, work):
    work.is_default_shipping = True
    with pytest.raises(IntegrityError):
        work.save()


def test_make_default_moves_one_default_and_leaves_the_other(address, work):
    work.make_default_shipping()

    address.refresh_from_db()
    work.refresh_from_db()
    assert work.is_default_shipping and not address.is_default_shipping
    assert address.is_default_billing and not work.is_default_billing


def test_make_default_billing(address, work):
    work.make_default_billing()

    address.refresh_from_db()
    assert not address.is_default_billing
    assert Address.objects.get(is_default_billing=True) == work


def test_deleting_a_default_leaves_no_default(address, work):
    address.delete()

    work.refresh_from_db()
    assert not work.is_default_shipping
    assert not work.is_default_billing


def test_defaults_are_per_user(address, other_customer):
    theirs = Address.objects.create(user=other_customer, **WORK)

    assert theirs.is_default_shipping and theirs.is_default_billing


def test_as_checkout_initial_uses_checkout_field_names(address):
    assert address.as_checkout_initial("billing") == {
        "billing_name": "Casey Monroe",
        "billing_street": "214 Synapse Street",
        "billing_line2": "",
        "billing_city": "Canyon",
        "billing_state": "TX",
        "billing_zip": "79015",
    }


def test_save_from_checkout_creates_then_skips_an_exact_duplicate(customer):
    data = {
        "shipping_name": "Casey Monroe",
        "shipping_street": "9 Axon Avenue",
        "shipping_line2": "",
        "shipping_city": "Norman",
        "shipping_state": "OK",
        "shipping_zip": "73019",
    }

    first = Address.objects.save_from_checkout(customer, data, "shipping")
    again = Address.objects.save_from_checkout(customer, data, "shipping")

    assert again == first
    assert customer.addresses.count() == 1
    assert first.label == ""


# --- The address book --------------------------------------------------------


def test_address_book_requires_login(client, db):
    response = client.get(reverse("accounts:addresses"))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))


def test_address_book_empty_state(client, customer):
    client.force_login(customer)

    response = client.get(reverse("accounts:addresses"))

    assert "No saved addresses yet" in response.content.decode()


def test_address_book_lists_only_my_addresses_with_badges(
    client, customer, address, other_customer
):
    Address.objects.create(user=other_customer, **{**WORK, "label": "Theirs"})
    client.force_login(customer)

    page = client.get(reverse("accounts:addresses")).content.decode()

    assert "Home" in page
    assert "Default shipping" in page
    assert "Default billing" in page
    assert "Theirs" not in page


def test_adding_an_address(client, customer):
    client.force_login(customer)

    response = client.post(reverse("accounts:address_create"), WORK)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:addresses")
    saved = customer.addresses.get()
    assert saved.label == "Work"
    assert saved.is_default_shipping  # the first address is both defaults


def test_an_invalid_address_shows_field_errors(client, customer):
    client.force_login(customer)

    response = client.post(
        reverse("accounts:address_create"), {**WORK, "zip_code": "790"}
    )

    assert response.status_code == HTTPStatus.OK
    assert "Enter a ZIP code like" in response.content.decode()
    assert not Address.objects.exists()


def test_editing_an_address(client, customer, address):
    client.force_login(customer)

    client.post(
        reverse("accounts:address_update", kwargs={"pk": address.pk}),
        {**WORK, "label": "Casa"},
    )

    address.refresh_from_db()
    assert address.label == "Casa"
    assert address.is_default_shipping  # editing leaves the defaults alone


def test_deleting_a_default_warns_first(client, customer, address):
    client.force_login(customer)
    url = reverse("accounts:address_delete", kwargs={"pk": address.pk})

    page = client.get(url).content.decode()
    assert "no default until you choose a new one" in page

    client.post(url)
    assert not Address.objects.exists()


def test_make_default_buttons(client, customer, address, work):
    client.force_login(customer)

    response = client.post(
        reverse("accounts:address_default_billing", kwargs={"pk": work.pk})
    )

    assert response.status_code == HTTPStatus.FOUND
    work.refresh_from_db()
    assert work.is_default_billing
    assert not work.is_default_shipping


def test_make_default_is_post_only(client, customer, work):
    client.force_login(customer)

    response = client.get(
        reverse("accounts:address_default_shipping", kwargs={"pk": work.pk})
    )

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.parametrize(
    ("name", "method"),
    [
        ("accounts:address_update", "get"),
        ("accounts:address_delete", "post"),
        ("accounts:address_default_shipping", "post"),
        ("accounts:address_default_billing", "post"),
    ],
)
def test_another_customers_address_is_not_found(
    client, address, other_customer, name, method
):
    client.force_login(other_customer)

    response = getattr(client, method)(reverse(name, kwargs={"pk": address.pk}))

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Address.objects.filter(pk=address.pk).exists()
