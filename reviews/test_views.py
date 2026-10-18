import re
from datetime import timedelta
from http import HTTPStatus

import pytest
from django.contrib.messages import get_messages
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

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


# --- Editing ------------------------------------------------------------------


def edit_url(product):
    return reverse("reviews:edit", kwargs={"slug": product.slug})


@pytest.mark.parametrize(
    ("data", "edited"),
    [
        pytest.param({"rating": "4", "comment": "Original"}, False, id="unchanged"),
        pytest.param(
            {"rating": "4", "comment": "  Original \n"}, False, id="only whitespace"
        ),
        pytest.param({"rating": "2", "comment": "Original"}, True, id="new rating"),
        pytest.param({"rating": "4", "comment": "Changed"}, True, id="new comment"),
    ],
)
def test_a_review_is_marked_edited_only_when_its_rating_or_comment_changes(
    client, customer, product, delivered_order, data, edited
):
    posted = timezone.now() - timedelta(days=3)
    review = Review.objects.create(
        user=customer, product=product, rating=4, comment="Original", created_at=posted
    )
    client.force_login(customer)
    before = timezone.now()

    response = client.post(edit_url(product), data)

    assert response.status_code == HTTPStatus.FOUND
    review.refresh_from_db()
    if edited:
        assert review.edited_at is not None and review.edited_at >= before
    else:
        assert review.edited_at is None
    assert review.created_at == posted


def test_an_unchanged_save_keeps_an_earlier_edit_time(
    client, customer, product, delivered_order
):
    edited = timezone.now() - timedelta(days=1)
    review = Review.objects.create(
        user=customer,
        product=product,
        rating=3,
        comment="Second thoughts",
        created_at=edited - timedelta(days=2),
        edited_at=edited,
    )
    client.force_login(customer)

    client.post(edit_url(product), {"rating": "3", "comment": "Second thoughts"})

    review.refresh_from_db()
    assert review.edited_at == edited


# --- Deleting -----------------------------------------------------------------


def delete_url(product):
    return reverse("reviews:delete", kwargs={"slug": product.slug})


def test_an_author_promoted_to_staff_can_delete_but_not_edit(
    client, customer, product, delivered_order
):
    review = Review.objects.create(
        user=customer, product=product, rating=4, comment="Written as a customer"
    )
    customer.is_staff = True
    customer.save()
    client.force_login(customer)

    confirmation = client.get(delete_url(product))
    assert confirmation.status_code == HTTPStatus.OK
    assert Review.objects.filter(pk=review.pk).exists()  # GET deletes nothing

    assert client.get(edit_url(product)).status_code == HTTPStatus.FORBIDDEN
    refused = client.post(edit_url(product), {"rating": "1", "comment": "Changed"})
    assert refused.status_code == HTTPStatus.FORBIDDEN
    review.refresh_from_db()
    assert (review.rating, review.comment) == (4, "Written as a customer")
    assert review.status == Review.Status.PUBLISHED

    deleted = client.post(delete_url(product))
    assert deleted.status_code == HTTPStatus.FOUND
    assert deleted.url == f"{product.get_absolute_url()}#reviews"
    assert not Review.objects.filter(pk=review.pk).exists()


def test_an_author_whose_order_was_cancelled_may_delete_but_not_edit(
    client, customer, product, delivered_order
):
    Review.objects.create(user=customer, product=product, rating=4, comment="Mine")
    delivered_order.status = Order.Status.CANCELLED
    delivered_order.save()
    client.force_login(customer)

    assert client.get(edit_url(product)).status_code == HTTPStatus.FORBIDDEN
    refused = client.post(edit_url(product), {"rating": "1", "comment": "Changed"})
    assert refused.status_code == HTTPStatus.FORBIDDEN
    assert Review.objects.get().comment == "Mine"

    assert client.post(delete_url(product)).status_code == HTTPStatus.FOUND
    assert not Review.objects.exists()


def test_the_eligible_author_of_a_hidden_review_may_delete_but_not_edit(
    client, customer, staff_user, product, delivered_order
):
    review = Review.objects.create(
        user=customer,
        product=product,
        rating=1,
        comment="Words staff hid",
        status=Review.Status.HIDDEN,
        hidden_by=staff_user,
        hidden_at=timezone.now(),
        hidden_reason="Off-topic",
    )
    client.force_login(customer)

    assert client.get(edit_url(product)).status_code == HTTPStatus.FORBIDDEN
    refused = client.post(edit_url(product), {"rating": "5", "comment": "Rewritten"})
    assert refused.status_code == HTTPStatus.FORBIDDEN
    review.refresh_from_db()
    assert (review.rating, review.comment) == (1, "Words staff hid")
    assert review.status == Review.Status.HIDDEN

    assert client.get(delete_url(product)).status_code == HTTPStatus.OK
    assert Review.objects.filter(pk=review.pk).exists()


# --- No review of yours to act on ---------------------------------------------


@pytest.mark.parametrize("url", [edit_url, delete_url], ids=["edit", "delete"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_a_visitor_without_a_review_of_the_product_gets_404(
    client, customer, other_customer, product, delivered_order, order_for, url, method
):
    """Even with another customer's review of the same product in place:
    the URL only ever reaches your own review, so theirs stays untouched."""
    order_for(other_customer, Order.Status.DELIVERED, product)
    theirs = Review.objects.create(
        user=other_customer, product=product, rating=5, comment="Not yours to touch"
    )
    client.force_login(customer)

    response = getattr(client, method)(url(product), {"rating": "1", "comment": "X"})

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "Not yours to touch" not in response.content.decode()
    theirs.refresh_from_db()
    assert (theirs.rating, theirs.comment) == (5, "Not yours to touch")
    assert Review.objects.count() == 1


@pytest.mark.parametrize("url", [edit_url, delete_url], ids=["edit", "delete"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_anonymous_visitors_to_edit_or_delete_are_sent_to_login(
    client, customer, product, url, method
):
    Review.objects.create(user=customer, product=product, rating=4, comment="Kept")

    response = getattr(client, method)(url(product), {"rating": "1"})

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))
    assert f"next={url(product)}" in response.url
    assert Review.objects.get().comment == "Kept"


# --- The edit form ------------------------------------------------------------


def test_the_edit_form_starts_from_the_current_review(
    client, customer, product, delivered_order
):
    Review.objects.create(
        user=customer, product=product, rating=3, comment="Current words"
    )
    client.force_login(customer)

    response = client.get(edit_url(product))

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert "Edit your review of" in page
    assert "Current words" in page
    assert response.context["form"]["rating"].value() == 3
    assert re.search(r'value="3"\s+class="radio"\s+checked', page)


def test_a_successful_edit_redirects_with_a_message(
    client, customer, product, delivered_order
):
    Review.objects.create(user=customer, product=product, rating=3, comment="Old")
    client.force_login(customer)

    response = client.post(edit_url(product), {"rating": "5", "comment": "  New  "})

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{product.get_absolute_url()}#reviews"
    assert [str(m) for m in get_messages(response.wsgi_request)] == [
        "Your review has been updated."
    ]
    review = Review.objects.get()
    assert (review.rating, review.comment) == (5, "New")


@pytest.mark.parametrize(
    ("data", "field"),
    [
        ({"comment": "No stars"}, "rating"),
        ({"rating": "4", "comment": "x" * 2001}, "comment"),
    ],
)
def test_an_invalid_edit_re_displays_and_changes_nothing(
    client, customer, product, delivered_order, data, field
):
    Review.objects.create(user=customer, product=product, rating=3, comment="Old")
    client.force_login(customer)

    response = client.post(edit_url(product), data)

    assert response.status_code == HTTPStatus.OK
    assert field in response.context["form"].errors
    review = Review.objects.get()
    assert (review.rating, review.comment, review.edited_at) == (3, "Old", None)


def test_editing_keeps_the_reviews_place_in_the_list(
    client, customer, other_customer, product, delivered_order
):
    now = timezone.now()
    mine = Review.objects.create(
        user=customer, product=product, rating=3, created_at=now - timedelta(days=5)
    )
    newer = Review.objects.create(
        user=other_customer, product=product, rating=4, created_at=now
    )
    client.force_login(customer)

    client.post(edit_url(product), {"rating": "5", "comment": "Updated"})

    assert list(Review.objects.all()) == [newer, mine]


# --- The delete flow ----------------------------------------------------------


def test_the_delete_page_asks_first_and_changes_nothing(
    client, customer, product, delivered_order
):
    Review.objects.create(user=customer, product=product, rating=4)
    client.force_login(customer)

    response = client.get(delete_url(product))

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert f"Delete your review of {product.name}?" in page
    assert 'method="post"' in page
    assert "csrfmiddlewaretoken" in page
    assert Review.objects.count() == 1


def test_deleting_redirects_with_a_message(client, customer, product, delivered_order):
    Review.objects.create(user=customer, product=product, rating=4)
    client.force_login(customer)

    response = client.post(delete_url(product))

    assert response.url == f"{product.get_absolute_url()}#reviews"
    assert [str(m) for m in get_messages(response.wsgi_request)] == [
        "Your review has been deleted."
    ]
    assert not Review.objects.exists()


def test_deleting_leaves_other_reviews_alone(
    client, customer, other_customer, product, delivered_order
):
    Review.objects.create(user=customer, product=product, rating=4)
    theirs = Review.objects.create(user=other_customer, product=product, rating=2)
    client.force_login(customer)

    client.post(delete_url(product))

    assert list(Review.objects.all()) == [theirs]


def test_after_deleting_an_eligible_customer_may_write_a_fresh_review(
    client, customer, product, delivered_order
):
    Review.objects.create(user=customer, product=product, rating=1, comment="Old take")
    client.force_login(customer)
    client.post(delete_url(product))

    form = client.get(create_url(product))
    response = client.post(create_url(product), {"rating": "5", "comment": "New take"})

    assert form.status_code == HTTPStatus.OK
    assert response.status_code == HTTPStatus.FOUND
    review = Review.objects.get()
    assert (review.rating, review.comment, review.edited_at) == (5, "New take", None)


def test_deleting_a_hidden_review_just_deletes_it_for_now(
    client, customer, staff_user, product, delivered_order
):
    """Phase 5 adds the repost restriction; until then nothing else changes."""
    Review.objects.create(
        user=customer,
        product=product,
        rating=1,
        status=Review.Status.HIDDEN,
        hidden_by=staff_user,
        hidden_at=timezone.now(),
        hidden_reason="Off-topic",
    )
    client.force_login(customer)

    assert client.post(delete_url(product)).status_code == HTTPStatus.FOUND
    assert not Review.objects.exists()
