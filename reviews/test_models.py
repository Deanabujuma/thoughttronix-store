from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Review


def hidden(**fields):
    """The moderation fields of a correctly hidden review."""
    return {
        "status": Review.Status.HIDDEN,
        "hidden_at": timezone.now(),
        "hidden_reason": "Off-topic",
        **fields,
    }


# --- Defaults -----------------------------------------------------------------


def test_a_new_review_is_published_with_no_moderation_record(customer, product):
    review = Review.objects.create(user=customer, product=product, rating=4)

    assert review.status == Review.Status.PUBLISHED
    assert review.hidden_by is None
    assert review.hidden_at is None
    assert review.hidden_reason == ""
    assert review.created_at is not None
    assert review.edited_at is None


# --- Database constraints -----------------------------------------------------


def test_the_database_allows_one_review_per_customer_per_product(customer, product):
    Review.objects.create(user=customer, product=product, rating=4)

    with pytest.raises(IntegrityError), transaction.atomic():
        Review.objects.create(user=customer, product=product, rating=2)


def test_another_customer_may_review_the_same_product(
    customer, other_customer, product
):
    Review.objects.create(user=customer, product=product, rating=4)
    Review.objects.create(user=other_customer, product=product, rating=2)

    assert Review.objects.count() == 2


@pytest.mark.parametrize("rating", [0, 6])
def test_the_database_rejects_a_rating_outside_one_to_five(customer, product, rating):
    with pytest.raises(IntegrityError), transaction.atomic():
        Review.objects.create(user=customer, product=product, rating=rating)


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param(hidden(hidden_at=None), id="hidden without hidden_at"),
        pytest.param(hidden(hidden_reason=""), id="hidden without a reason"),
        pytest.param({"hidden_at": timezone.now()}, id="published with a hidden_at"),
        pytest.param({"hidden_reason": "Spam"}, id="published with a reason"),
    ],
)
def test_the_database_rejects_a_status_that_disagrees_with_its_record(
    customer, product, fields
):
    with pytest.raises(IntegrityError), transaction.atomic():
        Review.objects.create(user=customer, product=product, rating=3, **fields)


def test_a_hidden_review_needs_no_moderator(customer, product):
    """hidden_by can become NULL, so status never depends on it."""
    review = Review.objects.create(
        user=customer, product=product, rating=3, **hidden(hidden_by=None)
    )

    assert review.status == Review.Status.HIDDEN


# --- Model validation ---------------------------------------------------------


def test_model_validation_rejects_a_rating_outside_one_to_five(customer, product):
    review = Review(user=customer, product=product, rating=6)

    with pytest.raises(ValidationError) as error:
        review.full_clean()

    assert "rating" in error.value.message_dict


def test_model_validation_rejects_a_comment_over_2000_characters(customer, product):
    review = Review(user=customer, product=product, rating=4, comment="x" * 2001)

    with pytest.raises(ValidationError) as error:
        review.full_clean()

    assert "comment" in error.value.message_dict


# --- Trimming -----------------------------------------------------------------


def test_the_comment_is_trimmed_on_save(customer, product):
    review = Review.objects.create(
        user=customer, product=product, rating=4, comment="  Works great.\n "
    )

    review.refresh_from_db()
    assert review.comment == "Works great."


def test_a_whitespace_only_comment_is_stored_empty(customer, product):
    review = Review.objects.create(
        user=customer, product=product, rating=4, comment=" \n\t "
    )

    review.refresh_from_db()
    assert review.comment == ""


# --- Querysets ----------------------------------------------------------------


def test_published_leaves_out_hidden_reviews(customer, other_customer, product):
    shown = Review.objects.create(user=customer, product=product, rating=4)
    Review.objects.create(user=other_customer, product=product, rating=1, **hidden())

    assert list(Review.objects.published()) == [shown]


def test_reviews_are_newest_first_then_newest_pk(product):
    users = [get_user_model().objects.create_user(username=f"r{n}") for n in range(3)]
    now = timezone.now()
    older = Review.objects.create(
        user=users[0], product=product, rating=4, created_at=now - timedelta(days=1)
    )
    tie_first = Review.objects.create(
        user=users[1], product=product, rating=4, created_at=now
    )
    tie_second = Review.objects.create(
        user=users[2], product=product, rating=4, created_at=now
    )

    assert list(Review.objects.all()) == [tie_second, tie_first, older]


def test_own_finds_only_the_visitors_review(customer, other_customer, product):
    mine = Review.objects.create(user=customer, product=product, rating=4)
    Review.objects.create(user=other_customer, product=product, rating=2)

    assert Review.objects.own(customer, product) == mine


def test_the_summary_of_a_product_without_reviews_is_empty(product):
    assert Review.objects.summary_for(product) == {"average": None, "count": 0}
