from datetime import timedelta
from decimal import Decimal
from http import HTTPStatus

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from products.models import Product

from .models import Wishlist, WishlistItem

WISHLIST_LINK = f'href="{reverse("wishlist:list")}"'


def test_no_wishlist_shows_the_empty_state_and_creates_none(client, customer):
    client.force_login(customer)

    page = client.get(reverse("wishlist:list")).content.decode()

    assert "Your wishlist is empty" in page
    assert not Wishlist.objects.exists()


def test_empty_wishlist_shows_the_empty_state(client, customer, wishlist):
    client.force_login(customer)

    page = client.get(reverse("wishlist:list")).content.decode()

    assert "Your wishlist is empty" in page
    assert f'href="{reverse("products:catalog")}"' in page


def test_list_page_requires_login(client, db):
    response = client.get(reverse("wishlist:list"))

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url
    assert not Wishlist.objects.exists()


def test_viewing_a_wishlist_changes_nothing(client, customer, saved_item):
    client.force_login(customer)

    client.get(reverse("wishlist:list"))

    assert Wishlist.objects.count() == 1
    assert list(WishlistItem.objects.all()) == [saved_item]


def test_items_are_newest_first_by_added_at(
    client, customer, wishlist, product, unavailable_product
):
    # Created first but saved later, so creation order can't stand in.
    now = timezone.now()
    newer = WishlistItem.objects.create(
        wishlist=wishlist, product=product, added_at=now
    )
    older = WishlistItem.objects.create(
        wishlist=wishlist,
        product=unavailable_product,
        added_at=now - timedelta(days=3),
    )
    client.force_login(customer)

    response = client.get(reverse("wishlist:list"))

    assert list(response.context["items"]) == [newer, older]
    page = response.content.decode()
    assert page.index(product.name) < page.index(unavailable_product.name)


def test_each_item_shows_image_name_price_availability_and_link(
    client, customer, saved_item, product, unavailable_product
):
    Wishlist.for_user(customer).save_product(unavailable_product)
    client.force_login(customer)

    page = client.get(reverse("wishlist:list")).content.decode()

    for item in (product, unavailable_product):
        assert f'href="{item.get_absolute_url()}"' in page
        assert item.name in page
        assert f'src="{item.card_image.url}"' in page
        assert f'alt="{item.card_image.alt}"' in page
    assert "$349.99" in page
    assert "$139.00" in page
    assert "In stock" in page
    assert "Unavailable" in page


def test_products_load_without_a_query_per_item(client, customer, wishlist, category):
    client.force_login(customer)

    def queries_for_page():
        with CaptureQueriesContext(connection) as queries:
            client.get(reverse("wishlist:list"))
        return len(queries)

    wishlist.save_product(
        Product.objects.create(
            name="Item 0", slug="item-0", price=Decimal("1.00"), category=category
        )
    )
    one_item = queries_for_page()
    for n in range(1, 5):
        wishlist.save_product(
            Product.objects.create(
                name=f"Item {n}",
                slug=f"item-{n}",
                price=Decimal("1.00"),
                category=category,
            )
        )

    assert queries_for_page() == one_item


def test_navbar_links_to_the_wishlist_when_signed_in(client, customer, product):
    client.force_login(customer)

    page = client.get(reverse("products:catalog")).content.decode()

    assert f'<a {WISHLIST_LINK} class="btn btn-ghost btn-sm">Wishlist</a>' in page


def test_navbar_has_no_wishlist_link_when_signed_out(client, product):
    page = client.get(reverse("products:catalog")).content.decode()

    assert WISHLIST_LINK not in page
