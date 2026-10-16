"""One shopper's actions never reach another shopper's wishlist."""

from decimal import Decimal

from django.urls import reverse

from products.models import Product

from .models import Wishlist, WishlistItem


def test_saving_never_touches_another_users_wishlist(
    client, other_customer, saved_item
):
    client.force_login(other_customer)

    client.post(reverse("wishlist:save", kwargs={"pk": saved_item.product.pk}))

    # The owner's item is untouched; the other user got their own wishlist.
    saved_item.refresh_from_db()
    assert saved_item.wishlist.user.username == "customer"
    assert saved_item.wishlist.items.count() == 1
    assert Wishlist.for_user(other_customer).items.count() == 1
    assert WishlistItem.objects.count() == 2


def test_removing_never_touches_another_users_wishlist(
    client, other_customer, saved_item
):
    client.force_login(other_customer)

    client.post(reverse("wishlist:remove", kwargs={"pk": saved_item.product.pk}))

    assert WishlistItem.objects.filter(pk=saved_item.pk).exists()
    assert not Wishlist.objects.filter(user=other_customer).exists()


def test_removing_when_both_saved_removes_only_your_own(
    client, customer, other_customer, saved_item
):
    product = saved_item.product
    Wishlist.for_user(other_customer).save_product(product)
    client.force_login(other_customer)

    client.post(reverse("wishlist:remove", kwargs={"pk": product.pk}))

    assert Wishlist.has_saved(customer, product)
    assert not Wishlist.has_saved(other_customer, product)


def test_list_page_shows_only_your_own_saved_products(
    client, customer, other_customer, saved_item, category
):
    pillow = Product.objects.create(
        name="Charging Pillow",
        slug="charging-pillow",
        price=Decimal("69.00"),
        category=category,
    )
    Wishlist.for_user(other_customer).save_product(pillow)
    client.force_login(customer)

    page = client.get(reverse("wishlist:list")).content.decode()

    assert saved_item.product.name in page
    assert pillow.name not in page


def test_detail_page_saved_state_is_per_user(client, other_customer, saved_item):
    client.force_login(other_customer)

    response = client.get(saved_item.product.get_absolute_url())

    assert response.context["saved"] is False
    assert "Saved — remove" not in response.content.decode()
