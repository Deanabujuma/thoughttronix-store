import io
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError
from django.urls import reverse
from django.utils.html import escape

from orders.models import CartItem, Order, OrderItem
from wishlist.models import Wishlist, WishlistItem

from .models import Category, Product, Tag

# --- Model behavior -------------------------------------------------------


def test_category_str(category):
    assert str(category) == "Home Assistants"


def test_product_str(product):
    assert str(product) == "Seraphine Home Hub"


def test_tag_str(tag):
    assert str(tag) == "bestseller"


def test_available_manager_excludes_unavailable(product, unavailable_product):
    available = Product.objects.available()

    assert product in available
    assert unavailable_product not in available


def test_search_matches_name_and_description(product, unavailable_product):
    assert product in Product.objects.search("home hub")
    assert product in Product.objects.search("seven-microphone")
    assert product not in Product.objects.search("death ray")


def test_product_slug_unique(product, category):
    with pytest.raises(IntegrityError):
        Product.objects.create(
            name="Another Hub",
            slug=product.slug,
            price=Decimal("1.00"),
            category=category,
        )


def test_product_get_absolute_url(product):
    assert product.get_absolute_url() == "/products/seraphine-home-hub/"


def test_category_get_absolute_url(category):
    assert category.get_absolute_url() == "/categories/home-assistants/"


# --- Catalog views ---------------------------------------------------------


def test_catalog_displays_product(client, product):
    """The catalog shows a product's name, category, tagline, and price."""
    response = client.get(reverse("products:catalog"))

    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert product.name in page
    assert product.category.name in page
    assert escape(product.tagline) in page
    assert str(product.price) in page
    assert product.get_absolute_url() in page


def test_detail_page(client, product):
    response = client.get(product.get_absolute_url())

    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert product.name in page
    assert escape(product.description) in page


def test_detail_unknown_slug_404(client, db):
    response = client.get(reverse("products:detail", kwargs={"slug": "no-such-thing"}))

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_detail_shows_availability(client, unavailable_product):
    response = client.get(unavailable_product.get_absolute_url())

    assert "Unavailable" in response.content.decode()


# --- The wishlist button on the detail page --------------------------------


def wishlist_button(page):
    """The wishlist control, from its opening tag through its closing tag."""
    start = page.rfind("<", 0, page.index('id="wishlist-button"'))
    end = min(
        i for i in (page.find("</a>", start), page.find("</button>", start)) if i != -1
    )
    return page[start:end]


def test_wishlist_button_signed_out_links_to_login(client, product):
    page = client.get(product.get_absolute_url()).content.decode()

    button = wishlist_button(page)
    login = reverse("accounts:login")
    assert button.startswith("<a ")
    assert f'href="{login}?next=/products/seraphine-home-hub/"' in button
    assert "btn btn-secondary btn-outline btn-sm" in button
    assert "♡</span> Save to wishlist" in button
    assert "hx-post" not in button


def test_wishlist_button_available_not_saved(client, customer, product):
    client.force_login(customer)

    response = client.get(product.get_absolute_url())

    button = wishlist_button(response.content.decode())
    assert response.context["saved"] is False
    assert f'hx-post="{reverse("wishlist:save", args=[product.pk])}"' in button
    assert 'hx-swap="outerHTML"' in button
    assert 'aria-pressed="false"' in button
    assert 'class="btn btn-secondary btn-outline btn-sm"' in button
    assert "♡</span> Save to wishlist" in button


@pytest.mark.parametrize("available", [True, False])
def test_wishlist_button_saved(client, customer, saved_item, product, available):
    product.is_available = available
    product.save()
    client.force_login(customer)

    response = client.get(product.get_absolute_url())

    button = wishlist_button(response.content.decode())
    assert response.context["saved"] is True
    assert f'hx-post="{reverse("wishlist:remove", args=[product.pk])}"' in button
    assert 'hx-swap="outerHTML"' in button
    assert 'aria-pressed="true"' in button
    assert 'class="btn btn-secondary btn-sm"' in button
    assert "♥</span> Saved — remove" in button


def test_wishlist_button_unavailable_not_saved(client, customer, unavailable_product):
    client.force_login(customer)

    page = client.get(unavailable_product.get_absolute_url()).content.decode()

    button = wishlist_button(page)
    assert "disabled" in button
    assert "hx-post" not in button
    assert "aria-pressed" not in button
    assert "btn-outline" in button
    assert "♡</span> Save to wishlist" in button
    # Only add-to-cart's button says "Unavailable" (the badge is the other).
    assert page.count(">Unavailable</button>") == 1


@pytest.mark.parametrize("signed_in", [True, False])
def test_viewing_a_product_never_creates_a_wishlist(
    client, customer, product, signed_in
):
    if signed_in:
        client.force_login(customer)

    client.get(product.get_absolute_url())

    assert not Wishlist.objects.exists()


FEATURED_BADGE = '<span class="badge badge-accent">Featured</span>'


def test_catalog_shows_featured_badge_only_on_featured(client, product):
    assert (
        FEATURED_BADGE not in client.get(reverse("products:catalog")).content.decode()
    )

    product.is_featured = True
    product.save()

    assert FEATURED_BADGE in client.get(reverse("products:catalog")).content.decode()


def test_detail_shows_featured_badge_only_on_featured(client, product):
    url = product.get_absolute_url()
    assert FEATURED_BADGE not in client.get(url).content.decode()

    product.is_featured = True
    product.save()

    assert FEATURED_BADGE in client.get(url).content.decode()


def test_category_page_lists_only_its_products(client, product):
    defense = Category.objects.create(name="Defense", slug="defense")
    Product.objects.create(
        name="SoulSear Mark II",
        slug="soulsear-mark-ii",
        price=Decimal("2400000.00"),
        category=defense,
    )

    response = client.get(defense.get_absolute_url())

    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert "SoulSear Mark II" in page
    assert product.name not in page


def test_category_unknown_slug_404(client, db):
    response = client.get(reverse("products:category", kwargs={"slug": "nope"}))

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_empty_category_shows_empty_state(client, db):
    empty = Category.objects.create(name="Defense", slug="defense")

    response = client.get(empty.get_absolute_url())

    assert "This shelf is empty" in response.content.decode()


# --- Search, filtering, and their composition ------------------------------


def test_search_filters_catalog(client, product, unavailable_product):
    response = client.get(reverse("products:catalog"), {"q": "home hub"})

    page = response.content.decode()
    assert product.name in page
    assert unavailable_product.name not in page


def test_search_no_results_shows_empty_state(client, product):
    response = client.get(reverse("products:catalog"), {"q": "death ray"})

    assert "Nothing matches" in response.content.decode()


def test_tag_filter(client, product, unavailable_product, tag):
    product.tags.add(tag)

    response = client.get(reverse("products:catalog"), {"tag": tag.slug})

    page = response.content.decode()
    assert product.name in page
    assert unavailable_product.name not in page


def test_search_and_tag_compose(client, product, unavailable_product, tag):
    product.tags.add(tag)
    unavailable_product.tags.add(tag)

    response = client.get(
        reverse("products:catalog"), {"tag": tag.slug, "q": "home hub"}
    )

    page = response.content.decode()
    assert product.name in page
    assert unavailable_product.name not in page


def test_category_querystring_filter(client, product):
    defense = Category.objects.create(name="Defense", slug="defense")
    Product.objects.create(
        name="SoulSear Mark II",
        slug="soulsear-mark-ii",
        price=Decimal("2400000.00"),
        category=defense,
    )

    response = client.get(reverse("products:catalog"), {"category": "defense"})

    page = response.content.decode()
    assert "SoulSear Mark II" in page
    assert product.name not in page


def test_catalog_paginates_at_twelve(client, category):
    for n in range(13):
        Product.objects.create(
            name=f"Widget {n:02d}",
            slug=f"widget-{n:02d}",
            price=Decimal("9.99"),
            category=category,
        )

    first = client.get(reverse("products:catalog"))
    second = client.get(reverse("products:catalog"), {"page": 2})

    assert len(first.context["products"]) == 12
    assert len(second.context["products"]) == 1
    assert "Page 2 of 2" in second.content.decode()


# --- The seed command -------------------------------------------------------


def test_uploads_go_to_a_temporary_media_root(settings, tmp_path):
    """The autouse fixture keeps every test — seed included — out of media/."""
    assert settings.MEDIA_ROOT == tmp_path / "media"


def test_seed_builds_the_demo_world(db):
    call_command("seed")

    assert Category.objects.count() == 6
    assert Tag.objects.count() == 12
    assert Product.objects.count() == 34

    User = get_user_model()
    admin = User.objects.get(username="admin")
    employee = User.objects.get(username="employee")
    customer = User.objects.get(username="customer")
    assert admin.is_superuser
    assert employee.is_staff and not employee.is_superuser
    assert employee.job_title == "Junior Thought Curator"
    assert not customer.is_staff
    assert customer.cart.item_count() == 4
    assert customer.orders.count() == 4

    mark_one = Product.objects.get(slug="soulsear-mark-i")
    assert not mark_one.is_available
    assert mark_one.category.name == "Defense"

    # 40–60 orders across the trailing six months, per the PRD.
    assert Order.objects.count() == 52
    statuses = set(Order.objects.values_list("status", flat=True))
    assert statuses == set(Order.Status.values)


def test_seed_is_idempotent(db):
    call_command("seed")
    first = (
        Category.objects.count(),
        Tag.objects.count(),
        Product.objects.count(),
        get_user_model().objects.count(),
        CartItem.objects.count(),
        Order.objects.count(),
        OrderItem.objects.count(),
        Wishlist.objects.count(),
        WishlistItem.objects.count(),
    )

    call_command("seed")
    second = (
        Category.objects.count(),
        Tag.objects.count(),
        Product.objects.count(),
        get_user_model().objects.count(),
        CartItem.objects.count(),
        Order.objects.count(),
        OrderItem.objects.count(),
        Wishlist.objects.count(),
        WishlistItem.objects.count(),
    )

    assert first == second


def demo_wishlist():
    """The demo customer's (slug, added_at) pairs, in the page's order."""
    customer = get_user_model().objects.get(username="customer")
    return [
        (item.product.slug, item.added_at) for item in customer.wishlist.items.all()
    ]


def test_seed_gives_the_customer_a_demo_wishlist(db):
    call_command("seed")

    # Newest first, with EchoPatch — saved before it was pulled — last.
    assert demo_wishlist() == [
        ("mindsync-duo", datetime(2026, 10, 14, 15, 0, tzinfo=UTC)),
        ("pulse-halo", datetime(2026, 10, 11, 18, 30, tzinfo=UTC)),
        ("recallpro", datetime(2026, 10, 4, 14, 15, tzinfo=UTC)),
        ("echopatch", datetime(2026, 9, 15, 20, 45, tzinfo=UTC)),
    ]
    unavailable = WishlistItem.objects.filter(product__is_available=False)
    assert [item.product.slug for item in unavailable] == ["echopatch"]


def test_seed_wishlist_is_identical_every_run(db):
    """Same products, same order, and the very same added_at values."""
    call_command("seed")
    first = demo_wishlist()

    call_command("seed")

    assert demo_wishlist() == first


def test_seed_leaves_only_the_demo_wishlist(other_customer, product):
    """Every wishlist goes — even one whose owner the seed doesn't manage."""
    Wishlist.for_user(other_customer).save_product(product)

    call_command("seed")

    customer = get_user_model().objects.get(username="customer")
    assert list(Wishlist.objects.all()) == [customer.wishlist]


def test_seed_success_message_mentions_the_wishlist(db):
    output = io.StringIO()

    call_command("seed", stdout=output)

    assert "a 4-item wishlist" in output.getvalue()
