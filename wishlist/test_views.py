from http import HTTPStatus

import pytest
from django.urls import reverse

from .models import Wishlist, WishlistItem


def save_url(product):
    return reverse("wishlist:save", kwargs={"pk": product.pk})


def remove_url(product):
    return reverse("wishlist:remove", kwargs={"pk": product.pk})


# --- POST only, sign-in required ---------------------------------------------


@pytest.mark.parametrize("url", [save_url, remove_url])
def test_get_is_refused(client, customer, product, url):
    client.force_login(customer)

    response = client.get(url(product))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert not Wishlist.objects.exists()


def test_anonymous_save_redirects_and_saves_nothing(client, product):
    response = client.post(save_url(product))

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url
    assert not Wishlist.objects.exists()


def test_anonymous_remove_redirects_and_removes_nothing(client, saved_item):
    response = client.post(remove_url(saved_item.product))

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url
    assert WishlistItem.objects.count() == 1


# --- Save ---------------------------------------------------------------------


def test_save_returns_the_saved_button_partial(client, customer, product):
    client.force_login(customer)

    response = client.post(save_url(product))

    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert "<html" not in page
    assert "Saved — remove" in page
    assert 'aria-pressed="true"' in page
    assert remove_url(product) in page
    assert Wishlist.has_saved(customer, product)


def test_save_creates_the_wishlist_when_needed(client, customer, product):
    client.force_login(customer)

    client.post(save_url(product))

    assert Wishlist.objects.get().user == customer


def test_saving_twice_keeps_one_item(client, customer, product):
    client.force_login(customer)
    client.post(save_url(product))

    response = client.post(save_url(product))

    assert "Saved — remove" in response.content.decode()
    assert WishlistItem.objects.count() == 1


def test_saving_an_unavailable_product_404s(client, customer, unavailable_product):
    client.force_login(customer)

    response = client.post(save_url(unavailable_product))

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert not WishlistItem.objects.exists()


def test_saving_an_unknown_product_404s(client, customer):
    client.force_login(customer)

    response = client.post(reverse("wishlist:save", kwargs={"pk": 9999}))

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert not Wishlist.objects.exists()


# --- Remove -------------------------------------------------------------------


def test_remove_returns_the_not_saved_button_partial(client, customer, saved_item):
    product = saved_item.product
    client.force_login(customer)

    response = client.post(remove_url(product))

    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert "<html" not in page
    assert "Save to wishlist" in page
    assert 'aria-pressed="false"' in page
    assert save_url(product) in page
    assert not WishlistItem.objects.exists()


def test_removing_an_unsaved_product_is_harmless(client, customer, product):
    client.force_login(customer)

    response = client.post(remove_url(product))

    assert response.status_code == HTTPStatus.OK
    assert 'aria-pressed="false"' in response.content.decode()
    assert not Wishlist.objects.exists()


def test_removing_a_product_that_became_unavailable(client, customer, saved_item):
    product = saved_item.product
    product.is_available = False
    product.save()
    client.force_login(customer)

    response = client.post(remove_url(product))

    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert not WishlistItem.objects.exists()
    # Now unsaved and not for sale: the disabled button that never posts.
    assert "disabled" in page
    assert "hx-post" not in page


def test_removing_an_unknown_product_404s(client, customer):
    client.force_login(customer)

    response = client.post(reverse("wishlist:remove", kwargs={"pk": 9999}))

    assert response.status_code == HTTPStatus.NOT_FOUND


# --- Every signed-in role -----------------------------------------------------


@pytest.mark.parametrize("user_fixture", ["customer", "staff_user", "admin_user"])
def test_every_role_can_save_and_remove(client, request, product, user_fixture):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)

    client.post(save_url(product))
    assert Wishlist.has_saved(user, product)

    client.post(remove_url(product))
    assert not Wishlist.has_saved(user, product)


# --- Django admin and the back office ----------------------------------------


def test_admin_lists_wishlists_with_items_inline(client, admin_user, saved_item):
    client.force_login(admin_user)

    changelist = client.get(
        reverse("admin:wishlist_wishlist_changelist"), {"q": "custom"}
    )
    change = client.get(
        reverse("admin:wishlist_wishlist_change", args=[saved_item.wishlist.pk])
    )

    assert changelist.status_code == HTTPStatus.OK
    assert "customer" in changelist.content.decode()
    assert change.status_code == HTTPStatus.OK
    (inline,) = change.context["inline_admin_formsets"]
    assert list(inline.formset.queryset) == [saved_item]


def test_admin_search_is_by_username(client, admin_user, saved_item, other_customer):
    Wishlist.for_user(other_customer)
    client.force_login(admin_user)

    response = client.get(reverse("admin:wishlist_wishlist_changelist"), {"q": "other"})

    assert list(response.context["cl"].result_list) == [other_customer.wishlist]


def test_staff_without_permissions_cannot_open_wishlists_in_admin(
    client, staff_user, saved_item
):
    client.force_login(staff_user)

    response = client.get(reverse("admin:wishlist_wishlist_changelist"))

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_back_office_has_no_wishlist_screen(client, staff_user):
    client.force_login(staff_user)

    response = client.get(reverse("dashboard:index"))

    # The storefront navbar links to your own wishlist on every page; the
    # back office itself — its tab rail and screens — has none.
    assert response.status_code == HTTPStatus.OK
    back_office = response.content.decode().split("</header>")[1]
    assert 'role="tablist"' in back_office
    assert "wishlist" not in back_office.lower()
