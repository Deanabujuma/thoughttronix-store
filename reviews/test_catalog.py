from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from products.models import Product, Tag

from .models import Review


def card_for(page, name):
    """The HTML of the one catalog card that shows ``name``."""
    (card,) = [c for c in page.split('<div class="card ') if f">{name}</a>" in c]
    return card


def make_product(category, name, *tags):
    product = Product.objects.create(
        name=name,
        slug=name.lower().replace(" ", "-"),
        price=Decimal("10.00"),
        category=category,
    )
    product.tags.set(tags)
    return product


def review(product, username, rating, **fields):
    user, _ = get_user_model().objects.get_or_create(username=username)
    return Review.objects.create(user=user, product=product, rating=rating, **fields)


def test_catalog_cards_show_published_only_ratings_under_search_and_filters(
    client, category, staff_user
):
    calm = Tag.objects.create(name="calm", slug="calm")
    bestseller = Tag.objects.create(name="bestseller", slug="bestseller")
    # Two tags on Halo One: a tag join must never double its reviews.
    halo_one = make_product(category, "Halo One", calm, bestseller)
    halo_two = make_product(category, "Halo Two", calm)
    make_product(category, "Halo Three", calm)  # no reviews
    quiet_box = make_product(category, "Quiet Box", calm)  # fails the search
    review(halo_one, "ana", 5)
    review(halo_one, "ben", 4)
    review(  # counted, it would make Halo One "3.3 … 3 reviews"
        halo_one,
        "cy",
        1,
        status=Review.Status.HIDDEN,
        hidden_by=staff_user,
        hidden_at=timezone.now(),
        hidden_reason="Off-topic",
    )
    review(halo_two, "ana", 2)
    review(quiet_box, "ben", 5)
    filters = {"q": "Halo", "tag": "calm"}
    urls = [
        reverse("products:catalog"),
        reverse("products:category", kwargs={"slug": category.slug}),
    ]

    for url in urls:
        page = client.get(url, filters).content.decode()

        assert 'aria-label="Rated 4.5 out of 5, 2 reviews"' in card_for(
            page, "Halo One"
        )
        assert 'aria-label="Rated 2.0 out of 5, 1 review"' in card_for(page, "Halo Two")
        assert "No reviews yet" in card_for(page, "Halo Three")
        assert "Quiet Box" not in page

    # The same request shape with three times the cards (all still on one
    # page) must cost the same number of queries: none per card.
    with CaptureQueriesContext(connection) as three_cards:
        client.get(urls[0], filters)
    for n in range(6):
        extra = make_product(category, f"Halo Extra {n}", calm, bestseller)
        review(extra, f"extra{n}", 3)
    with CaptureQueriesContext(connection) as nine_cards:
        page = client.get(urls[0], filters).content.decode()

    assert page.count('class="card ') == 9
    assert len(nine_cards) == len(three_cards)


def test_an_unavailable_product_still_shows_its_rating(
    client, category, unavailable_product
):
    review(unavailable_product, "ana", 3)
    review(unavailable_product, "ben", 4)
    urls = [
        reverse("products:catalog"),
        reverse("products:category", kwargs={"slug": category.slug}),
    ]

    for url in urls:
        card = card_for(client.get(url).content.decode(), unavailable_product.name)
        assert "Unavailable" in card
        assert 'aria-label="Rated 3.5 out of 5, 2 reviews"' in card


def test_a_card_whose_reviews_are_all_hidden_says_no_reviews_yet(
    client, product, staff_user
):
    review(
        product,
        "ana",
        5,
        status=Review.Status.HIDDEN,
        hidden_by=staff_user,
        hidden_at=timezone.now(),
        hidden_reason="Off-topic",
    )

    card = card_for(
        client.get(reverse("products:catalog")).content.decode(), product.name
    )

    assert "No reviews yet" in card
    assert "Rated" not in card


def test_ratings_are_right_on_the_catalogs_second_page(client, category):
    """The catalog's own ?page= still pages, and its cards keep their ratings."""
    for n in range(13):  # the catalog shows 12 a page
        review(make_product(category, f"Item {n:02}"), f"buyer{n:02}", 4)

    response = client.get(reverse("products:catalog"), {"page": 2})

    (only,) = response.context["products"]
    card = card_for(response.content.decode(), only.name)
    assert 'aria-label="Rated 4.0 out of 5, 1 review"' in card
