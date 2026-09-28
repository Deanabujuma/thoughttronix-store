"""Discount codes: normalization, status, the redeem validator, the math."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db.models import ProtectedError
from django.utils import timezone

from products.models import Product

from .models import Coupon, InvalidCouponError
from .services import place_order
from .test_checkout_form import VALID_DATA

pytestmark = pytest.mark.django_db


def make_coupon(code="SPRING10", percent_off=10, days_left=30, **fields):
    return Coupon.objects.create(
        code=code,
        percent_off=percent_off,
        expires_on=timezone.localdate() + timedelta(days=days_left),
        **fields,
    )


# --- The code itself -----------------------------------------------------------


def test_codes_are_stored_trimmed_and_uppercased():
    coupon = make_coupon(code="  spring10 ")

    assert coupon.code == "SPRING10"


def test_status_follows_retired_expired_live_precedence(
    whole_order_coupon, expired_coupon, retired_coupon
):
    both = make_coupon(code="OLD-AND-OFF", days_left=-5, is_active=False)

    assert whole_order_coupon.status == Coupon.Status.LIVE
    assert expired_coupon.status == Coupon.Status.EXPIRED
    assert retired_coupon.status == Coupon.Status.RETIRED
    assert both.status == Coupon.Status.RETIRED


def test_status_querysets_partition_the_codes(
    whole_order_coupon, expired_coupon, retired_coupon
):
    assert list(Coupon.objects.live()) == [whole_order_coupon]
    assert list(Coupon.objects.expired()) == [expired_coupon]
    assert list(Coupon.objects.retired()) == [retired_coupon]
    assert Coupon.objects.with_status("bogus").count() == 3


# --- redeem: the one validator ---------------------------------------------------


def test_a_live_code_redeems_whatever_its_case_or_spacing(
    cart, cart_item, whole_order_coupon
):
    assert Coupon.objects.redeem("  thoughts10 ", cart) == whole_order_coupon


def test_an_unknown_code_is_not_recognized(cart, cart_item):
    with pytest.raises(InvalidCouponError, match="We don't recognize the code BOGUS."):
        Coupon.objects.redeem("bogus", cart)


def test_a_retired_code_is_no_longer_available(cart, cart_item, retired_coupon):
    with pytest.raises(InvalidCouponError, match="LAUNCH25 is no longer available."):
        Coupon.objects.redeem("LAUNCH25", cart)


def test_an_expired_code_names_its_expiry_date(cart, cart_item):
    make_coupon(code="SUMMER20", days_left=-1)
    yesterday = timezone.localdate() - timedelta(days=1)

    with pytest.raises(InvalidCouponError) as caught:
        Coupon.objects.redeem("SUMMER20", cart)

    assert str(caught.value) == (
        f"SUMMER20 expired on {yesterday:%b} {yesterday.day}, {yesterday.year}."
    )


def test_a_code_is_valid_through_its_expiry_date(cart, cart_item):
    coupon = make_coupon(days_left=0)

    assert Coupon.objects.redeem("SPRING10", cart) == coupon


def test_retired_wins_over_expired(cart, cart_item):
    make_coupon(code="OLD-AND-OFF", days_left=-5, is_active=False)

    with pytest.raises(InvalidCouponError, match="no longer available"):
        Coupon.objects.redeem("OLD-AND-OFF", cart)


def test_invalid_coupon_errors_are_value_errors():
    assert issubclass(InvalidCouponError, ValueError)


# --- The math ---------------------------------------------------------------------


def test_a_line_discount_rounds_half_up_to_the_cent(product):
    coupon = make_coupon(percent_off=10)

    # 10% of 12.25 is 1.225 — half-up gives 1.23 (banker's rounding, 1.22).
    assert coupon.discount_for(product, Decimal("12.25"), 1) == Decimal("1.23")


def test_a_line_discount_covers_every_unit(product):
    coupon = make_coupon(percent_off=10)

    assert coupon.discount_for(product, Decimal("349.99"), 2) == Decimal("70.00")


def test_cart_pricing_sums_line_discounts(cart, cart_item, whole_order_coupon):
    pricing = cart.priced(whole_order_coupon)

    assert pricing.subtotal == Decimal("699.98")
    assert pricing.discount == Decimal("70.00")
    assert pricing.total == Decimal("629.98")
    assert pricing.discount == sum(line.discount for line in pricing.lines)


def test_cart_pricing_without_a_coupon_is_the_cart_total(cart, cart_item):
    pricing = cart.priced()

    assert pricing.discount == Decimal("0.00")
    assert pricing.total == cart.total()


# --- Product scope ------------------------------------------------------------------


@pytest.fixture
def cable(category):
    return Product.objects.create(
        name="Aria Cable",
        slug="aria-cable",
        price=Decimal("25.00"),
        category=category,
    )


def test_a_product_code_discounts_only_eligible_lines(
    cart, cart_item, cable, product_coupon
):
    cart.items.create(product=cable, quantity=2)

    pricing = cart.priced(product_coupon)

    hub, cables = pricing.lines
    assert hub.discount == Decimal("105.00")  # 15% of 2 × 349.99, every unit
    assert cables.discount == Decimal("0.00")  # full price
    assert pricing.total == Decimal("699.98") + Decimal("50.00") - Decimal("105.00")


def test_a_product_code_redeems_when_an_eligible_product_is_in_the_cart(
    cart, cart_item, cable, product_coupon
):
    cart.items.create(product=cable)

    assert Coupon.objects.redeem("HUB15", cart) == product_coupon


def test_a_product_code_without_its_product_names_it(cart, cable, product_coupon):
    cart.items.create(product=cable)

    with pytest.raises(InvalidCouponError) as caught:
        Coupon.objects.redeem("HUB15", cart)

    assert str(caught.value) == (
        "HUB15 applies to Seraphine Home Hub, which isn't in your cart."
    )


def test_a_long_product_list_is_shortened(cart, category, cable):
    coupon = make_coupon(code="GADGETS", applies_to=Coupon.AppliesTo.PRODUCTS)
    for name in ["Echo A", "Echo B", "Echo C", "Echo D", "Echo E"]:
        coupon.products.add(
            Product.objects.create(
                name=name,
                slug=name.lower().replace(" ", "-"),
                price=1,
                category=category,
            )
        )
    cart.items.create(product=cable)

    with pytest.raises(InvalidCouponError) as caught:
        Coupon.objects.redeem("GADGETS", cart)

    assert str(caught.value) == (
        "GADGETS applies to Echo A, Echo B, Echo C and 2 more, "
        "none of which are in your cart."
    )


def test_a_short_product_list_is_named_in_full(cart, category, cable):
    coupon = make_coupon(code="PAIR", applies_to=Coupon.AppliesTo.PRODUCTS)
    for name in ["Echo A", "Echo B"]:
        coupon.products.add(
            Product.objects.create(
                name=name,
                slug=name.lower().replace(" ", "-"),
                price=1,
                category=category,
            )
        )
    cart.items.create(product=cable)

    with pytest.raises(InvalidCouponError, match="applies to Echo A and Echo B, none"):
        Coupon.objects.redeem("PAIR", cart)


def test_expired_wins_over_no_eligible_product(cart, cable, product_coupon):
    product_coupon.expires_on = timezone.localdate() - timedelta(days=1)
    product_coupon.save()
    cart.items.create(product=cable)

    with pytest.raises(InvalidCouponError, match="expired on"):
        Coupon.objects.redeem("HUB15", cart)


# --- Use and deletion ---------------------------------------------------------------


def test_a_used_code_cannot_be_deleted(cart, cart_item, whole_order_coupon):
    place_order(cart, cart.user, dict(VALID_DATA), coupon_code="THOUGHTS10")

    assert whole_order_coupon.is_used
    with pytest.raises(ProtectedError):
        whole_order_coupon.delete()


def test_an_unused_code_can_be_deleted(whole_order_coupon):
    assert not whole_order_coupon.is_used

    whole_order_coupon.delete()

    assert not Coupon.objects.exists()
