"""Back-office discount codes: access, the list, create/edit rules, retire, delete."""

from datetime import timedelta
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from .models import Coupon
from .services import place_order
from .test_checkout_form import VALID_DATA

pytestmark = pytest.mark.django_db

LIST = reverse("orders:manage_coupons")
CREATE = reverse("orders:manage_coupon_create")


def update_url(coupon):
    return reverse("orders:manage_coupon_update", kwargs={"pk": coupon.pk})


def form_data(**overrides):
    return {
        "code": "SPRING10",
        "percent_off": "10",
        "applies_to": Coupon.AppliesTo.ORDER,
        "expires_on": (timezone.localdate() + timedelta(days=30)).isoformat(),
        "is_active": "on",
        **overrides,
    }


@pytest.fixture
def used_coupon(cart, cart_item, whole_order_coupon):
    """THOUGHTS10, after one order used it."""
    place_order(cart, cart.user, dict(VALID_DATA), coupon_code="THOUGHTS10")
    return whole_order_coupon


@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client


# --- Access control ------------------------------------------------------------


def coupon_urls(coupon):
    return [
        LIST,
        CREATE,
        update_url(coupon),
        reverse("orders:manage_coupon_retire", kwargs={"pk": coupon.pk}),
        reverse("orders:manage_coupon_delete", kwargs={"pk": coupon.pk}),
    ]


def test_anonymous_users_are_sent_to_login(client, whole_order_coupon):
    for url in coupon_urls(whole_order_coupon):
        response = client.get(url)

        assert response.status_code == HTTPStatus.FOUND, url
        assert reverse("accounts:login") in response.url


def test_customers_get_403(client, customer, whole_order_coupon):
    client.force_login(customer)

    for url in coupon_urls(whole_order_coupon):
        assert client.get(url).status_code == HTTPStatus.FORBIDDEN, url


def test_the_back_office_has_a_discount_codes_tab(staff_client):
    page = staff_client.get(LIST).content.decode()

    assert "Discount codes" in page
    assert "tab-active" in page


# --- The list ---------------------------------------------------------------------


def test_the_list_shows_every_code_with_status_scope_and_uses(
    staff_client, used_coupon, product_coupon, expired_coupon, retired_coupon
):
    response = staff_client.get(LIST)

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    for code in ["THOUGHTS10", "HUB15", "SUMMER20", "LAUNCH25"]:
        assert code in page
    assert "Whole order" in page
    assert "1 product" in page
    uses = {coupon.code: coupon.use_count for coupon in response.context["coupons"]}
    assert uses == {"THOUGHTS10": 1, "HUB15": 0, "SUMMER20": 0, "LAUNCH25": 0}


@pytest.mark.parametrize(
    ("status", "expected"),
    [("live", {"THOUGHTS10"}), ("expired", {"SUMMER20"}), ("retired", {"LAUNCH25"})],
)
def test_the_status_filter(
    staff_client, whole_order_coupon, expired_coupon, retired_coupon, status, expected
):
    response = staff_client.get(LIST, {"status": status})

    assert {coupon.code for coupon in response.context["coupons"]} == expected


def test_an_unknown_status_shows_everything(
    staff_client, whole_order_coupon, expired_coupon
):
    response = staff_client.get(LIST, {"status": "bogus"})

    assert len(response.context["coupons"]) == 2
    assert response.context["active_status"] == ""


def test_uses_count_cancelled_orders_too(staff_client, used_coupon):
    used_coupon.orders.update(status="CANCELLED")

    response = staff_client.get(LIST)

    assert response.context["coupons"][0].use_count == 1


def test_delete_is_offered_only_for_unused_codes_and_retire_for_used(
    staff_client, used_coupon, expired_coupon
):
    page = staff_client.get(LIST).content.decode()

    delete_unused = reverse(
        "orders:manage_coupon_delete", kwargs={"pk": expired_coupon.pk}
    )
    delete_used = reverse("orders:manage_coupon_delete", kwargs={"pk": used_coupon.pk})
    retire_used = reverse("orders:manage_coupon_retire", kwargs={"pk": used_coupon.pk})
    assert delete_unused in page
    assert delete_used not in page
    assert retire_used in page


def test_the_list_has_a_designed_empty_state(staff_client):
    page = staff_client.get(LIST).content.decode()

    assert "No discount codes yet" in page
    assert CREATE in page


def test_an_empty_filter_has_its_own_empty_state(staff_client, whole_order_coupon):
    page = staff_client.get(LIST, {"status": "retired"}).content.decode()

    assert "No retired codes" in page
    assert "Show all codes" in page


# --- Create -------------------------------------------------------------------------


def test_staff_can_create_a_whole_order_code(staff_client):
    response = staff_client.post(CREATE, form_data(code="spring10"))

    assert response.status_code == HTTPStatus.FOUND
    coupon = Coupon.objects.get()
    assert coupon.code == "SPRING10"
    assert coupon.percent_off == 10
    assert coupon.is_active


def test_staff_can_create_a_product_code(staff_client, product):
    staff_client.post(
        CREATE,
        form_data(applies_to=Coupon.AppliesTo.PRODUCTS, products=[product.pk]),
    )

    assert list(Coupon.objects.get().products.all()) == [product]


def test_selected_products_requires_a_product(staff_client):
    response = staff_client.post(
        CREATE, form_data(applies_to=Coupon.AppliesTo.PRODUCTS)
    )

    assert response.context["form"].errors["products"] == [
        "Pick at least one product, or change “Applies to” to Whole order."
    ]
    assert not Coupon.objects.exists()


def test_a_whole_order_code_cannot_have_products(staff_client, product):
    response = staff_client.post(CREATE, form_data(products=[product.pk]))

    assert response.context["form"].errors["products"] == [
        "Whole-order codes can't have products selected."
    ]


def test_code_names_are_unique_whatever_the_case(staff_client, retired_coupon):
    response = staff_client.post(CREATE, form_data(code="launch25"))

    assert "code" in response.context["form"].errors
    assert Coupon.objects.count() == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("percent_off", "0"),
        ("percent_off", "100"),
        ("code", "AB"),
        ("code", "SPRING 10"),
        ("code", "SPRING_10!"),
        ("expires_on", ""),
    ],
)
def test_each_rule_rejects_bad_input(staff_client, field, value):
    response = staff_client.post(CREATE, form_data(**{field: value}))

    assert field in response.context["form"].errors
    assert not Coupon.objects.exists()


# --- Edit ---------------------------------------------------------------------------


def test_an_unused_code_is_fully_editable(staff_client, whole_order_coupon):
    staff_client.post(
        update_url(whole_order_coupon), form_data(code="THOUGHTS15", percent_off="15")
    )

    whole_order_coupon.refresh_from_db()
    assert whole_order_coupon.code == "THOUGHTS15"
    assert whole_order_coupon.percent_off == 15


def test_a_used_codes_terms_are_locked(staff_client, used_coupon, product):
    response = staff_client.get(update_url(used_coupon))
    form = response.context["form"]
    assert all(form.fields[name].disabled for name in form.LOCKED_AFTER_USE)
    assert "used on 1 order" in response.content.decode()

    staff_client.post(
        update_url(used_coupon),
        form_data(
            code="FREEBIE",
            percent_off="90",
            applies_to=Coupon.AppliesTo.PRODUCTS,
            products=[product.pk],
        ),
    )

    used_coupon.refresh_from_db()
    assert used_coupon.code == "THOUGHTS10"
    assert used_coupon.percent_off == 10
    assert used_coupon.applies_to == Coupon.AppliesTo.ORDER
    assert not used_coupon.products.exists()


def test_a_used_codes_timing_stays_editable(staff_client, used_coupon):
    new_expiry = timezone.localdate() + timedelta(days=90)

    staff_client.post(
        update_url(used_coupon),
        {**form_data(expires_on=new_expiry.isoformat()), "is_active": ""},
    )

    used_coupon.refresh_from_db()
    assert used_coupon.expires_on == new_expiry
    assert not used_coupon.is_active


def test_a_retired_code_can_be_switched_back_on(staff_client, retired_coupon):
    staff_client.post(
        update_url(retired_coupon), form_data(code="LAUNCH25", percent_off="25")
    )

    retired_coupon.refresh_from_db()
    assert retired_coupon.is_active


# --- Retire and delete ----------------------------------------------------------------


def test_retiring_switches_the_code_off_and_keeps_past_orders(
    staff_client, used_coupon
):
    order = used_coupon.orders.get()

    response = staff_client.post(
        reverse("orders:manage_coupon_retire", kwargs={"pk": used_coupon.pk})
    )

    assert response.status_code == HTTPStatus.FOUND
    used_coupon.refresh_from_db()
    assert used_coupon.status == Coupon.Status.RETIRED
    order.refresh_from_db()
    assert order.discount_amount == Decimal("70.00")


def test_an_unused_code_can_be_deleted(staff_client, whole_order_coupon):
    url = reverse("orders:manage_coupon_delete", kwargs={"pk": whole_order_coupon.pk})

    assert staff_client.get(url).status_code == HTTPStatus.OK
    staff_client.post(url)

    assert not Coupon.objects.exists()


def test_a_used_code_cannot_be_deleted(staff_client, used_coupon):
    url = reverse("orders:manage_coupon_delete", kwargs={"pk": used_coupon.pk})

    assert staff_client.get(url).status_code == HTTPStatus.NOT_FOUND
    assert staff_client.post(url).status_code == HTTPStatus.NOT_FOUND
    assert Coupon.objects.filter(pk=used_coupon.pk).exists()


# --- The staff order page ---------------------------------------------------------------


def test_the_staff_order_page_links_the_code(staff_client, used_coupon):
    order = used_coupon.orders.get()

    page = staff_client.get(
        reverse("orders:manage_order_detail", kwargs={"pk": order.pk})
    ).content.decode()

    assert f'href="{update_url(used_coupon)}"' in page
    assert "−$70.00 with THOUGHTS10" in page
