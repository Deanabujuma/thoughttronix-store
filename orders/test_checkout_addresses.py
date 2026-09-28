"""Saved addresses at checkout: defaults filled in, the HTMX picker, saving."""

from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Address

from .models import Order
from .test_checkout_form import VALID_DATA


@pytest.fixture
def work(customer, address):
    return Address.objects.create(
        user=customer,
        label="Work",
        name="Casey Monroe",
        street="1 Neural Plaza",
        line2="Floor 12",
        city="Amarillo",
        state="TX",
        zip_code="79101",
    )


def test_checkout_opens_with_both_defaults_filled_in(client, address, work, cart_item):
    work.make_default_billing()
    client.force_login(address.user)

    form = client.get(reverse("orders:checkout")).context["form"]

    assert form["shipping_street"].value() == "214 Synapse Street"
    assert form["billing_street"].value() == "1 Neural Plaza"
    assert form["billing_line2"].value() == "Floor 12"


def test_checkout_without_saved_addresses_opens_empty(client, customer, cart_item):
    client.force_login(customer)

    response = client.get(reverse("orders:checkout"))

    assert response.context["form"]["shipping_street"].value() is None
    assert "Use a saved address" not in response.content.decode()


def test_checkout_shows_the_saved_address_picker(client, address, work, cart_item):
    client.force_login(address.user)

    page = client.get(reverse("orders:checkout")).content.decode()

    assert reverse("orders:checkout_address", kwargs={"kind": "shipping"}) in page
    assert "Use a saved address" in page
    assert "Work" in page


def test_the_picker_returns_that_address_as_filled_fields(client, work):
    client.force_login(work.user)

    response = client.get(
        reverse("orders:checkout_address", kwargs={"kind": "billing"}),
        {"address": work.pk},
    )

    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert 'name="billing_street"' in page
    assert 'value="1 Neural Plaza"' in page
    assert "shipping_street" not in page
    assert "<html" not in page  # a partial, never the full base.html


@pytest.mark.parametrize(
    ("kind", "address_param"),
    [("shipping", "abc"), ("shipping", ""), ("gift", None)],
)
def test_the_picker_404s_on_bad_input(client, address, kind, address_param):
    client.force_login(address.user)
    param = address.pk if address_param is None else address_param

    response = client.get(
        reverse("orders:checkout_address", kwargs={"kind": kind}),
        {"address": param},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_the_picker_never_serves_another_customers_address(client, address):
    other = get_user_model().objects.create_user(username="other", password="x")
    client.force_login(other)

    response = client.get(
        reverse("orders:checkout_address", kwargs={"kind": "shipping"}),
        {"address": address.pk},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_ticking_save_stores_the_address_as_the_first_default(
    client, customer, cart_item
):
    client.force_login(customer)

    client.post(reverse("orders:checkout"), {**VALID_DATA, "save_shipping": "on"})

    assert Order.objects.exists()
    saved = customer.addresses.get()
    assert saved.street == "12 Cortex Lane"
    assert saved.line2 == "Unit 7"
    assert saved.is_default_shipping and saved.is_default_billing


def test_saving_both_identical_addresses_stores_one(client, customer, cart_item):
    same_billing = {
        **VALID_DATA,
        "billing_line2": "Unit 7",
        "billing_zip": "79015",
        "save_shipping": "on",
        "save_billing": "on",
    }
    client.force_login(customer)

    client.post(reverse("orders:checkout"), same_billing)

    assert customer.addresses.count() == 1


def test_saving_a_known_address_is_skipped(client, address, cart_item):
    client.force_login(address.user)
    data = {
        **VALID_DATA,
        **address.as_checkout_initial("shipping"),
        "save_shipping": "on",
    }

    client.post(reverse("orders:checkout"), data)

    assert address.user.addresses.count() == 1


def test_unticked_boxes_save_nothing(client, customer, cart_item):
    client.force_login(customer)

    client.post(reverse("orders:checkout"), VALID_DATA)

    assert Order.objects.exists()
    assert not Address.objects.exists()


def test_orders_keep_their_copy_when_the_address_changes(client, address, cart_item):
    client.force_login(address.user)
    client.post(
        reverse("orders:checkout"),
        {**VALID_DATA, **address.as_checkout_initial("shipping")},
    )

    address.street = "99 Elsewhere Road"
    address.save()
    address.delete()

    assert Order.objects.get().shipping_street == "214 Synapse Street"
