"""The checkout's discount-code preview: HTMX Apply and Remove."""

from decimal import Decimal
from http import HTTPStatus

import pytest
from django.urls import reverse

from .models import Order
from .test_checkout_form import VALID_DATA

pytestmark = pytest.mark.django_db

PREVIEW = reverse("orders:checkout_coupon")


def apply(client, code):
    return client.post(PREVIEW, {"coupon_code": code})


def test_the_preview_requires_login(client):
    response = apply(client, "THOUGHTS10")

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url


def test_the_preview_is_post_only(client, customer):
    client.force_login(customer)

    assert client.get(PREVIEW).status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_applying_a_code_previews_the_discounted_order(
    client, customer, cart_item, whole_order_coupon
):
    client.force_login(customer)

    response = apply(client, "thoughts10")

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert "THOUGHTS10 applied — 10% off your order." in page
    assert 'value="THOUGHTS10"' in page and "readonly" not in page
    assert 'name="applied_coupon_code" value="THOUGHTS10"' in page
    assert "Apply" in page and "Remove" in page  # replace it, or take it off
    assert "−$70.00 with THOUGHTS10" in page  # the line
    assert "Discount (THOUGHTS10, 10%)" in page  # the summary
    assert "Place order — $629.98" in page  # the button
    assert page.count('hx-swap-oob="true"') == 2
    assert "<html" not in page  # a partial, never base.html


def test_the_preview_saves_nothing(
    client, customer, cart, cart_item, whole_order_coupon
):
    client.force_login(customer)

    apply(client, "THOUGHTS10")

    assert not Order.objects.exists()
    assert cart.items.get().quantity == 2


def test_a_failed_apply_shows_the_error_and_keeps_no_code(
    client, customer, cart_item, expired_coupon
):
    client.force_login(customer)

    response = apply(client, "SUMMER20")

    page = response.content.decode()
    assert "SUMMER20 expired on" in page
    assert 'value="SUMMER20"' not in page  # the field is back to empty
    assert 'name="applied_coupon_code" value=""' in page
    assert "Place order — $699.98" in page


def test_a_product_code_previews_its_eligible_lines_only(
    client, customer, cart_item, product_coupon
):
    client.force_login(customer)

    response = apply(client, "HUB15")

    page = response.content.decode()
    assert "15% off selected products." in page
    assert "−$105.00 with HUB15" in page


def test_remove_clears_the_code_without_an_error(
    client, customer, cart_item, whole_order_coupon
):
    client.force_login(customer)

    response = apply(client, "")

    page = response.content.decode()
    assert "text-error" not in page
    assert "Apply" in page
    assert "Place order — $699.98" in page


def test_applying_over_an_applied_code_replaces_it(
    client, customer, cart_item, whole_order_coupon, product_coupon
):
    client.force_login(customer)

    response = client.post(
        PREVIEW, {"coupon_code": "HUB15", "applied_coupon_code": "THOUGHTS10"}
    )

    page = response.content.decode()
    assert "HUB15 applied — 15% off selected products." in page
    assert 'name="applied_coupon_code" value="HUB15"' in page
    assert "THOUGHTS10 applied" not in page
    assert "Place order — $594.98" in page


def test_replacing_with_a_bad_code_drops_the_old_discount(
    client, customer, cart_item, whole_order_coupon, expired_coupon
):
    client.force_login(customer)

    response = client.post(
        PREVIEW, {"coupon_code": "SUMMER20", "applied_coupon_code": "THOUGHTS10"}
    )

    page = response.content.decode()
    assert "SUMMER20 expired on" in page
    assert "THOUGHTS10 applied" not in page
    assert "Discount (THOUGHTS10" not in page  # gone from the summary too
    assert 'name="applied_coupon_code" value=""' in page
    assert "Place order — $699.98" in page
    assert response.context["pricing"].total == Decimal("699.98")


# --- The full checkout page ---------------------------------------------------------


def test_the_checkout_page_offers_the_apply_control(client, customer, cart_item):
    client.force_login(customer)

    page = client.get(reverse("orders:checkout")).content.decode()

    assert 'id="coupon-field"' in page
    assert PREVIEW in page
    assert "Place order — $699.98" in page


def test_a_rerendered_checkout_keeps_a_valid_code_applied(
    client, customer, cart_item, whole_order_coupon
):
    client.force_login(customer)
    bad_card = {**VALID_DATA, "card_number": "4242 4242 4242 4241"}

    response = client.post(
        reverse("orders:checkout"), {**bad_card, "coupon_code": "THOUGHTS10"}
    )

    page = response.content.decode()
    assert "Enter a valid card number." in page
    assert "THOUGHTS10 applied" in page
    assert "Place order — $629.98" in page
    assert response.context["pricing"].total == Decimal("629.98")


def test_a_code_typed_over_but_never_applied_places_nothing(
    client, customer, cart_item, whole_order_coupon, product_coupon
):
    """Submitting a new code without Apply re-prices; it never charges blind."""
    client.force_login(customer)

    response = client.post(
        reverse("orders:checkout"),
        {**VALID_DATA, "coupon_code": "HUB15", "applied_coupon_code": "THOUGHTS10"},
    )

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert not Order.objects.exists()
    assert "Your discount changed" in page
    assert "HUB15 applied" in page
    assert 'name="applied_coupon_code" value="HUB15"' in page
    assert "Place order — $594.98" in page


def test_a_bad_code_typed_over_an_applied_one_clears_the_discount(
    client, customer, cart_item, whole_order_coupon, expired_coupon
):
    client.force_login(customer)

    response = client.post(
        reverse("orders:checkout"),
        {**VALID_DATA, "coupon_code": "SUMMER20", "applied_coupon_code": "THOUGHTS10"},
    )

    assert not Order.objects.exists()
    assert (
        response.context["coupon_form"]
        .errors["coupon_code"][0]
        .startswith("SUMMER20 expired on")
    )
    assert response.context["pricing"].total == Decimal("699.98")
    assert "Place order — $699.98" in response.content.decode()


def test_the_previewed_code_places_the_order(
    client, customer, cart_item, product_coupon
):
    client.force_login(customer)

    response = client.post(
        reverse("orders:checkout"),
        {**VALID_DATA, "coupon_code": "HUB15", "applied_coupon_code": "HUB15"},
    )

    assert response.status_code == HTTPStatus.FOUND
    assert Order.objects.get().total == Decimal("594.98")
