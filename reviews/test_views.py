from http import HTTPStatus

import pytest
from django.contrib.messages import get_messages
from django.db import IntegrityError
from django.urls import reverse

from orders.models import Order

from .forms import ReviewForm
from .models import Review


def create_url(product):
    return reverse("reviews:create", kwargs={"slug": product.slug})


@pytest.fixture
def other_tab_wins(customer, product, monkeypatch):
    """A race: the other tab's review lands just before this one saves.

    Both requests passed the eligibility check while no review existed.
    The other tab's row is written once this form has validated — after
    every check, but before the view's savepoint opens — so it survives
    the losing insert's rollback, as a committed row would.
    """
    clean = ReviewForm.clean

    def land_first(form):
        Review.objects.create(
            user=customer, product=product, rating=5, comment="Other tab"
        )
        return clean(form)

    monkeypatch.setattr(ReviewForm, "clean", land_first)


# --- Duplicate submissions ---------------------------------------------------


@pytest.mark.parametrize("submission", ["repeated", "concurrent"])
def test_a_duplicate_submission_keeps_one_review_and_never_500s(
    client, customer, product, delivered_order, request, submission
):
    client.force_login(customer)
    client.raise_request_exception = False  # a crash must show up as a 500
    if submission == "repeated":
        client.post(create_url(product), {"rating": 5, "comment": "Other tab"})
    else:
        request.getfixturevalue("other_tab_wins")

    response = client.post(create_url(product), {"rating": 2, "comment": "Second"})

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{product.get_absolute_url()}#reviews"
    assert "You've already reviewed this product." in [
        str(message) for message in get_messages(response.wsgi_request)
    ]
    assert Review.objects.get().comment == "Other tab"


def test_an_unrelated_integrity_error_is_re_raised(
    client, customer, product, delivered_order, monkeypatch
):
    """Only the duplicate-review race is handled; any other error surfaces."""

    def broken_save(review, *args, **kwargs):
        raise IntegrityError("CHECK constraint failed: some_other_rule")

    monkeypatch.setattr(Review, "save", broken_save)
    client.force_login(customer)

    with pytest.raises(IntegrityError, match="some_other_rule"):
        client.post(create_url(product), {"rating": 4})

    assert not Review.objects.exists()


# --- Who may open the form ----------------------------------------------------


@pytest.mark.parametrize("method", ["get", "post"])
def test_anonymous_visitors_are_sent_to_login(client, product, method):
    response = getattr(client, method)(create_url(product), {"rating": 4})

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))
    assert f"next={create_url(product)}" in response.url
    assert not Review.objects.exists()


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("status", [Order.Status.PLACED, Order.Status.SHIPPED])
def test_a_customer_who_hasnt_received_it_is_refused(
    client, customer, product, order_for, method, status
):
    order_for(customer, status, product)
    client.force_login(customer)

    response = getattr(client, method)(create_url(product), {"rating": 4})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert not Review.objects.exists()


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("role", ["is_staff", "is_superuser"])
def test_staff_and_the_admin_are_refused_even_with_a_delivered_order(
    client, customer, product, delivered_order, method, role
):
    setattr(customer, role, True)
    customer.save()
    client.force_login(customer)

    response = getattr(client, method)(create_url(product), {"rating": 4})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert not Review.objects.exists()


def test_an_unknown_product_is_404(client, customer):
    client.force_login(customer)

    response = client.get(reverse("reviews:create", kwargs={"slug": "no-such-thing"}))

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_an_author_opening_the_form_again_is_sent_back_to_their_review(
    client, customer, product, delivered_order
):
    Review.objects.create(user=customer, product=product, rating=4)
    client.force_login(customer)

    response = client.get(create_url(product))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{product.get_absolute_url()}#reviews"


def test_an_unavailable_product_can_still_be_reviewed(
    client, customer, unavailable_product, order_for
):
    order_for(customer, Order.Status.DELIVERED, unavailable_product)
    client.force_login(customer)

    response = client.post(create_url(unavailable_product), {"rating": 3})

    assert response.status_code == HTTPStatus.FOUND
    assert Review.objects.filter(product=unavailable_product).exists()


# --- The form -----------------------------------------------------------------


def test_the_form_offers_five_labeled_star_radios(
    client, customer, product, delivered_order
):
    client.force_login(customer)

    page = client.get(create_url(product)).content.decode()

    assert "<legend" in page and "Your rating</legend>" in page
    assert page.count('type="radio"') == 5
    for value, words in enumerate(["1 star", "2 stars", "3 stars", "4 stars"], 1):
        # A real <label for> names each radio; the glyphs are decoration.
        assert f'<label for="id_rating_{value - 1}"' in page
        assert f'value="{value}"' in page
        assert f"<span>{words}</span>" in page
    assert "<span>5 stars</span>" in page
    assert '<span class="text-lg text-warning" aria-hidden="true">★★★★☆</span>' in page
    assert "<script" not in page.split("<form")[1].split("</form>")[0]


def test_a_valid_review_is_saved_and_live_at_once(
    client, customer, product, delivered_order
):
    client.force_login(customer)

    response = client.post(
        create_url(product), {"rating": "5", "comment": "  Life-changing.  "}
    )

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{product.get_absolute_url()}#reviews"
    assert [str(m) for m in get_messages(response.wsgi_request)] == [
        "Thanks — your review is live."
    ]
    review = Review.objects.get()
    assert (review.user, review.product) == (customer, product)
    assert review.rating == 5
    assert review.comment == "Life-changing."
    assert review.status == Review.Status.PUBLISHED


def test_a_comment_is_optional(client, customer, product, delivered_order):
    client.force_login(customer)

    client.post(create_url(product), {"rating": "2"})

    assert Review.objects.get().comment == ""


@pytest.mark.parametrize(
    ("data", "field", "error"),
    [
        ({"comment": "No stars"}, "rating", "Choose a rating from 1 to 5 stars."),
        ({"rating": "0"}, "rating", "Choose a rating from 1 to 5 stars."),
        ({"rating": "6"}, "rating", "Choose a rating from 1 to 5 stars."),
        ({"rating": "4.5"}, "rating", "Choose a rating from 1 to 5 stars."),
        (
            {"rating": "4", "comment": "x" * 2001},
            "comment",
            "Ensure this value has at most 2000 characters (it has 2001).",
        ),
    ],
)
def test_invalid_input_re_displays_the_form_with_its_error(
    client, customer, product, delivered_order, data, field, error
):
    client.force_login(customer)

    response = client.post(create_url(product), data)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors[field] == [error]
    assert error in response.content.decode()
    assert not Review.objects.exists()


def test_a_2000_character_comment_is_accepted(
    client, customer, product, delivered_order
):
    client.force_login(customer)

    client.post(create_url(product), {"rating": "4", "comment": "x" * 2000})

    assert len(Review.objects.get().comment) == 2000
