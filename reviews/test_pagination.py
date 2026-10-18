from datetime import timedelta
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from orders.models import Order

from .models import Review


@pytest.fixture
def eleven_reviews(product, order_for):
    """Eleven regular customers, each with their own Delivered order for the
    product and one published review — enough for a second page.

    Comments run "Review 01" (newest) to "Review 11" (oldest), a day apart.
    Built in the test database only; the seed can't reach this many.
    """
    now = timezone.now()
    reviews = []
    for n in range(1, 12):
        user = get_user_model().objects.create_user(username=f"reviewer{n:02}")
        order_for(user, Order.Status.DELIVERED, product)
        reviews.append(
            Review.objects.create(
                user=user,
                product=product,
                rating=4,
                comment=f"Review {n:02}",
                created_at=now - timedelta(days=n),
            )
        )
    return reviews


def page(client, product, number=None):
    url = product.get_absolute_url()
    if number:
        url += f"?reviews={number}"
    return client.get(url).content.decode()


@pytest.mark.parametrize("viewer", ["anonymous", "author"])
def test_ten_reviews_a_page_newest_first_with_the_oldest_on_page_two(
    client, customer, product, delivered_order, eleven_reviews, viewer
):
    if viewer == "author":
        # The newest review of all: if it leaked into the list, it would
        # push "Review 10" off page 1.
        Review.objects.create(
            user=customer, product=product, rating=5, comment="My own review"
        )
        client.force_login(customer)
    newest_ten = [f"Review {n:02}" for n in range(1, 11)]

    first = page(client, product)
    second = page(client, product, 2)

    positions = [first.index(comment) for comment in newest_ten]
    assert positions == sorted(positions)  # newest first
    assert "Review 11" not in first

    assert "Review 11" in second
    for comment in newest_ten:
        assert comment not in second

    if viewer == "author":
        for shown in [first, second]:
            assert shown.count("My own review") == 1
            assert shown.index("Your review") < shown.index("My own review")


@pytest.mark.parametrize(
    ("value", "shows"),
    [
        pytest.param("abc", "first", id="not a number"),
        pytest.param("", "first", id="empty"),
        pytest.param("99", "last", id="past the end"),
        pytest.param("0", "last", id="zero"),
        pytest.param("-1", "last", id="negative"),
    ],
)
def test_a_bad_page_number_falls_back_and_never_errors(
    client, product, eleven_reviews, value, shows
):
    """Not a number → page 1; out of range → the last page (the PRD's rule)."""
    client.raise_request_exception = False  # a crash must show up as a 500

    response = client.get(product.get_absolute_url(), {"reviews": value})

    assert response.status_code == HTTPStatus.OK
    shown = response.content.decode()
    if shows == "first":
        assert all(f"Review {n:02}" in shown for n in range(1, 11))
        assert "Review 11" not in shown
    else:
        assert "Review 11" in shown
        assert not any(f"Review {n:02}" in shown for n in range(1, 11))


# --- Newer / Older links ------------------------------------------------------

NEWER = "← Newer reviews"
OLDER = "Older reviews →"


def more_reviews(product, order_for, count, start):
    """``count`` more eligible reviewers, older than the fixture's eleven."""
    now = timezone.now()
    for n in range(start, start + count):
        user = get_user_model().objects.create_user(username=f"reviewer{n:02}")
        order_for(user, Order.Status.DELIVERED, product)
        Review.objects.create(
            user=user,
            product=product,
            rating=3,
            comment=f"Review {n:02}",
            created_at=now - timedelta(days=n),
        )


def test_page_one_links_only_to_older_reviews(client, product, eleven_reviews):
    shown = page(client, product)

    assert 'aria-label="Review pages"' in shown
    assert 'href="?reviews=2#reviews" rel="next"' in shown
    assert OLDER in shown
    assert NEWER not in shown
    assert "Page 1 of 2" in shown


def test_the_last_page_links_only_to_newer_reviews(client, product, eleven_reviews):
    shown = page(client, product, 2)

    assert 'href="?reviews=1#reviews" rel="prev"' in shown
    assert NEWER in shown
    assert OLDER not in shown
    assert "Page 2 of 2" in shown


def test_a_middle_page_links_both_ways(client, product, eleven_reviews, order_for):
    more_reviews(product, order_for, 10, start=12)  # 21 reviews: three pages

    shown = page(client, product, 2)

    assert 'href="?reviews=1#reviews" rel="prev"' in shown
    assert 'href="?reviews=3#reviews" rel="next"' in shown
    assert "Page 2 of 3" in shown
    assert "Review 11" in shown and "Review 20" in shown
    assert "Review 10" not in shown and "Review 21" not in shown


def test_a_fallback_page_links_from_where_it_landed(client, product, eleven_reviews):
    """?reviews=99 shows the last page, and its links follow from there."""
    shown = page(client, product, 99)

    assert "Page 2 of 2" in shown
    assert 'href="?reviews=1#reviews" rel="prev"' in shown


def test_ten_reviews_or_fewer_need_no_page_links(client, product, order_for):
    more_reviews(product, order_for, 10, start=1)

    shown = page(client, product)

    assert "Review 10" in shown
    assert 'aria-label="Review pages"' not in shown
    assert NEWER not in shown and OLDER not in shown


def test_the_authors_review_stays_pinned_and_uncounted_on_every_page(
    client, customer, product, delivered_order, eleven_reviews
):
    """Eleven others plus the author still make two pages of public reviews:
    the author's review is pinned, never one of a page's ten."""
    Review.objects.create(
        user=customer, product=product, rating=5, comment="My own review"
    )
    client.force_login(customer)

    for number in [1, 2]:
        shown = page(client, product, number)
        assert f"Page {number} of 2" in shown
        assert shown.count("My own review") == 1
        assert shown.index("Your review") < shown.index("My own review")
        assert shown.index("My own review") < shown.index('aria-label="Review pages"')
