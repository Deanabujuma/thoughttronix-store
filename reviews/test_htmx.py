"""Inline HTMX review actions (Phase 7).

The same create, edit and delete URLs serve two kinds of request. With the
``HX-Request`` header they answer with partials for the product page;
without it, they behave exactly as the page tests in ``test_views.py`` say.
"""

import html
import re
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from orders.models import Order

from .forms import ReviewForm
from .models import Review, ReviewRestriction

HTMX = {"HX-Request": "true"}


def action_url(name, product):
    return reverse(f"reviews:{name}", kwargs={"slug": product.slug})


def oob_rating_summary(page):
    """The text after the out-of-band ``#rating-summary`` element's opening
    tag, or ``None`` if the response has no such element."""
    for tag in re.finditer(r"<[^>]*\bid=\"rating-summary\"[^>]*>", page):
        if 'hx-swap-oob="true"' in tag.group(0):
            return page[tag.end() :]
    return None


# --- Behavior 1: a successful inline action updates the section and summary --


@pytest.mark.parametrize(
    ("action", "own_review", "data", "summary", "shows", "message"),
    [
        pytest.param(
            "create",
            None,
            {"rating": "4", "comment": "Inline and instant."},
            "Rated 3.0 out of 5, 2 reviews",
            ["Your review", "Inline and instant."],
            "Thanks — your review is live.",
            id="create",
        ),
        pytest.param(
            "edit",
            {"rating": 4, "comment": "Before."},
            {"rating": "5", "comment": "After."},
            "Rated 3.5 out of 5, 2 reviews",
            ["Your review", "After.", "Edited"],
            "Your review has been updated.",
            id="edit",
        ),
        pytest.param(
            "delete",
            {"rating": 4, "comment": "Soon gone."},
            {},
            "Rated 2.0 out of 5, 1 review",
            ["Write a review"],
            "Your review has been deleted.",
            id="delete",
        ),
    ],
)
def test_a_successful_inline_action_swaps_the_reviews_section_and_summary(
    client,
    customer,
    other_customer,
    product,
    delivered_order,
    action,
    own_review,
    data,
    summary,
    shows,
    message,
):
    # Another shopper's 2-star review keeps the summary meaningful throughout.
    Review.objects.create(user=other_customer, product=product, rating=2)
    if own_review:
        Review.objects.create(user=customer, product=product, **own_review)
    client.force_login(customer)

    response = client.post(action_url(action, product), data, headers=HTMX)

    # A partial for the page to swap in, not a redirect or a whole page.
    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert "<html" not in page
    # It replaces the whole #reviews section.
    assert response.headers.get("HX-Retarget") == "#reviews"
    assert response.headers.get("HX-Reswap") == "outerHTML"
    assert 'id="reviews"' in page
    for text in shows:
        assert text in page
    assert message in page
    # The summary near the price updates out of band, with the new numbers.
    oob = oob_rating_summary(page)
    assert oob is not None, "no out-of-band #rating-summary in the response"
    assert f'aria-label="{summary}"' in oob
    # The change really happened, exactly once.
    mine = Review.objects.filter(user=customer, product=product)
    if action == "delete":
        assert not mine.exists()
    else:
        assert (mine.get().rating, mine.get().comment) == (
            int(data["rating"]),
            data["comment"],
        )
    assert Review.objects.filter(user=other_customer).count() == 1


# --- Behavior 2: invalid and duplicate inline submissions change nothing ------

RATING_ERROR = "Choose a rating from 1 to 5 stars."
LENGTH_ERROR = "Ensure this value has at most 2000 characters (it has 2001)."


@pytest.mark.parametrize(
    ("action", "data", "error"),
    [
        pytest.param(
            "create", {"comment": "No stars"}, RATING_ERROR, id="create-no-rating"
        ),
        pytest.param("create", {"rating": "6"}, RATING_ERROR, id="create-rating-6"),
        pytest.param(
            "create",
            {"rating": "4", "comment": "x" * 2001},
            LENGTH_ERROR,
            id="create-too-long",
        ),
        pytest.param(
            "edit", {"comment": "No stars"}, RATING_ERROR, id="edit-no-rating"
        ),
        pytest.param(
            "edit",
            {"rating": "4", "comment": "x" * 2001},
            LENGTH_ERROR,
            id="edit-too-long",
        ),
    ],
)
def test_an_invalid_inline_form_shows_its_errors_in_place_and_changes_nothing(
    client, customer, product, delivered_order, action, data, error
):
    if action == "edit":
        Review.objects.create(user=customer, product=product, rating=3, comment="Old")
    client.force_login(customer)
    url = action_url(action, product)

    response = client.post(url, data, headers=HTMX)

    # Only the form comes back, with its error, to replace itself in place.
    assert response.status_code == HTTPStatus.OK
    page = response.content.decode()
    assert "<html" not in page
    assert "HX-Retarget" not in response.headers
    assert f'hx-post="{url}"' in page
    assert "csrfmiddlewaretoken" in page
    assert error in html.unescape(page)
    # Nothing was saved or changed.
    if action == "create":
        assert not Review.objects.exists()
    else:
        review = Review.objects.get()
        assert (review.rating, review.comment, review.edited_at) == (3, "Old", None)


@pytest.fixture
def other_tab_wins(customer, product, monkeypatch):
    """A race, as in ``test_views.py``: the other tab's review lands after
    this form validates but before the view's savepoint opens."""
    clean = ReviewForm.clean

    def land_first(form):
        Review.objects.create(
            user=customer, product=product, rating=5, comment="Other tab"
        )
        return clean(form)

    monkeypatch.setattr(ReviewForm, "clean", land_first)


@pytest.mark.parametrize("submission", ["repeated", "concurrent"])
def test_a_duplicate_inline_submission_answers_in_place_with_one_review(
    client, customer, product, delivered_order, request, submission
):
    client.force_login(customer)
    client.raise_request_exception = False  # a crash must show up as a 500
    url = action_url("create", product)
    if submission == "repeated":
        client.post(url, {"rating": "5", "comment": "Other tab"}, headers=HTMX)
    else:
        request.getfixturevalue("other_tab_wins")

    response = client.post(url, {"rating": "2", "comment": "Second"}, headers=HTMX)

    # No redirect and no server error: the section, telling them why.
    assert response.status_code == HTTPStatus.OK
    page = html.unescape(response.content.decode())
    assert "<html" not in page
    assert response.headers.get("HX-Retarget") == "#reviews"
    assert response.headers.get("HX-Reswap") == "outerHTML"
    assert "You've already reviewed this product." in page
    assert "Your review" in page
    # One review, and it's still the first one.
    review = Review.objects.get()
    assert (review.rating, review.comment) == (5, "Other tab")


# --- Behavior 3: under HTMX, refusals keep their meaning ----------------------


def stored_data():
    """Every review and restriction, field by field — to prove a refused
    request changed nothing at all."""
    return (
        list(Review.objects.order_by("pk").values()),
        list(ReviewRestriction.objects.order_by("pk").values()),
    )


SUBMISSION = {"rating": "1", "comment": "Should never be saved."}


def hide(review, by):
    review.status = Review.Status.HIDDEN
    review.hidden_by, review.hidden_at = by, timezone.now()
    review.hidden_reason = "Off-topic"
    review.save()


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("action", ["create", "edit", "delete"])
def test_an_anonymous_inline_request_goes_to_login_and_changes_nothing(
    client, customer, product, delivered_order, action, method
):
    Review.objects.create(user=customer, product=product, rating=4, comment="Kept")
    before = stored_data()
    url = action_url(action, product)

    response = getattr(client, method)(url, SUBMISSION, headers=HTMX)

    # Not a 302: HTMX would follow it and swap the login page into the
    # target. HTMX goes to the login page itself, coming back here after.
    assert response.status_code == HTTPStatus.NO_CONTENT
    target = response.headers.get("HX-Redirect", "")
    assert target.startswith(reverse("accounts:login"))
    assert f"next={url}" in target
    assert stored_data() == before


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize(
    ("action", "case"),
    [
        ("create", "not yet received"),
        ("create", "staff"),
        ("create", "admin"),
        ("edit", "author promoted to staff"),
        ("edit", "author's order cancelled"),
        ("edit", "author's review hidden"),
    ],
)
def test_a_refused_inline_request_is_403_and_changes_nothing(
    client, customer, staff_user, product, order_for, action, case, method
):
    order = order_for(customer, Order.Status.DELIVERED, product)
    if case == "not yet received":
        order.status = Order.Status.SHIPPED
        order.save()
    elif case in ("staff", "admin"):
        customer.is_staff = True
        customer.is_superuser = case == "admin"
        customer.save()
    else:
        review = Review.objects.create(
            user=customer, product=product, rating=4, comment="Mine"
        )
        if case == "author promoted to staff":
            customer.is_staff = True
            customer.save()
        elif case == "author's order cancelled":
            order.status = Order.Status.CANCELLED
            order.save()
        else:
            hide(review, staff_user)
    before = stored_data()
    client.force_login(customer)

    response = getattr(client, method)(
        action_url(action, product), SUBMISSION, headers=HTMX
    )

    # Still 403. HTMX doesn't swap an error, so the page reloads itself
    # into its true state.
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.headers.get("HX-Refresh") == "true"
    assert stored_data() == before


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("action", ["edit", "delete"])
def test_an_inline_request_without_a_review_of_your_own_is_404(
    client,
    customer,
    other_customer,
    product,
    delivered_order,
    order_for,
    action,
    method,
):
    """Another customer's review of the product is there, and untouched."""
    order_for(other_customer, Order.Status.DELIVERED, product)
    Review.objects.create(
        user=other_customer, product=product, rating=5, comment="Not yours to touch"
    )
    before = stored_data()
    client.force_login(customer)

    response = getattr(client, method)(
        action_url(action, product), SUBMISSION, headers=HTMX
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers.get("HX-Refresh") == "true"
    assert "Not yours to touch" not in response.content.decode()
    assert stored_data() == before


@pytest.mark.parametrize(
    "case",
    ["author promoted to staff", "author's order cancelled", "author's review hidden"],
)
def test_an_author_who_cannot_edit_can_still_delete_inline(
    client, customer, staff_user, product, delivered_order, case
):
    review = Review.objects.create(
        user=customer, product=product, rating=4, comment="Mine"
    )
    if case == "author promoted to staff":
        customer.is_staff = True
        customer.save()
    elif case == "author's order cancelled":
        delivered_order.status = Order.Status.CANCELLED
        delivered_order.save()
    else:
        hide(review, staff_user)
    client.force_login(customer)

    response = client.post(action_url("delete", product), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("HX-Retarget") == "#reviews"
    assert "Your review has been deleted." in response.content.decode()
    assert not Review.objects.exists()
    # Deleting a hidden review still can't bypass moderation.
    restricted = ReviewRestriction.objects.filter(user=customer, product=product)
    assert restricted.exists() is (case == "author's review hidden")


# --- The rest of Phase 7: triggers, inline pieces, headers, security ---------


def restores_section(product):
    """The attributes Cancel and Keep it carry inline."""
    return (
        f'hx-get="{product.get_absolute_url()}" hx-select="#reviews" '
        'hx-target="#reviews" hx-swap="outerHTML"'
    )


@pytest.mark.parametrize(
    ("has_review", "triggers"),
    [(False, ["create"]), (True, ["edit", "delete"])],
    ids=["eligible", "author"],
)
def test_each_trigger_keeps_its_link_and_loads_inline(
    client, customer, product, delivered_order, has_review, triggers
):
    if has_review:
        Review.objects.create(user=customer, product=product, rating=4)
    client.force_login(customer)

    page = client.get(product.get_absolute_url()).content.decode()

    assert 'id="your-review"' in page
    for name in triggers:
        url = action_url(name, product)
        # Without JavaScript the href opens the page; with it, HTMX loads
        # the same URL into "Your review".
        assert f'href="{url}" hx-get="{url}" hx-target="#your-review"' in page


@pytest.mark.parametrize(
    ("action", "heading"),
    [
        ("create", "Write a review"),
        ("edit", "Edit your review"),
        ("delete", "Delete your review of Seraphine Home Hub?"),
    ],
)
def test_an_inline_get_loads_just_the_form_or_confirmation(
    client, customer, product, delivered_order, action, heading
):
    if action != "create":
        Review.objects.create(
            user=customer, product=product, rating=3, comment="Current words"
        )
    before = stored_data()
    client.force_login(customer)
    url = action_url(action, product)

    response = client.get(url, headers=HTMX)

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert "<html" not in page
    assert heading in page
    assert f'hx-post="{url}"' in page
    assert "csrfmiddlewaretoken" in page
    # Cancel / Keep it put the section back, from the product page itself.
    assert restores_section(product) in page
    if action == "edit":
        assert "Current words" in page
        assert re.search(r'value="3"\s+class="radio"\s+checked', page)
    assert stored_data() == before  # opening it never changes anything


@pytest.mark.parametrize("action", ["create", "edit", "delete"])
def test_the_standalone_pages_stay_free_of_htmx(
    client, customer, product, delivered_order, action
):
    """The no-JavaScript path: whole pages, plain forms, plain links."""
    if action != "create":
        Review.objects.create(user=customer, product=product, rating=3)
    client.force_login(customer)

    page = client.get(action_url(action, product)).content.decode()

    assert "<html" in page
    for attribute in ("hx-post", "hx-get", "hx-select", "hx-target"):
        assert attribute not in page


@pytest.mark.parametrize(
    "request_kind",
    [
        "page",
        "inline form",
        "inline success",
        "plain success",
        "inline 403",
        "inline login",
        "inline 404",
    ],
)
def test_every_answer_varies_on_hx_request(
    client, customer, other_customer, product, delivered_order, request_kind
):
    """One URL answers HTMX and plain requests differently, so caches must
    keep the two apart."""
    if request_kind != "inline login":
        client.force_login(customer)
    create, edit = action_url("create", product), action_url("edit", product)
    data = {"rating": "4"}
    if request_kind == "page":
        response = client.get(create)
    elif request_kind == "inline form":
        response = client.get(create, headers=HTMX)
    elif request_kind == "inline success":
        response = client.post(create, data, headers=HTMX)
    elif request_kind == "plain success":
        response = client.post(create, data)
    elif request_kind == "inline 403":
        client.force_login(other_customer)  # never received the product
        response = client.post(create, data, headers=HTMX)
    elif request_kind == "inline login":
        response = client.post(create, data, headers=HTMX)
    else:
        response = client.get(edit, headers=HTMX)  # no review of their own

    assert "HX-Request" in response.headers.get("Vary", "")


@pytest.mark.parametrize("action", ["create", "edit", "delete"])
def test_an_inline_post_needs_its_csrf_token(
    customer, product, delivered_order, action
):
    if action != "create":
        Review.objects.create(user=customer, product=product, rating=3, comment="Old")
    before = stored_data()
    client = Client(enforce_csrf_checks=True)
    client.force_login(customer)
    url = action_url(action, product)
    data = {"rating": "5", "comment": "New"}

    forged = client.post(url, data, headers=HTMX)

    assert forged.status_code == HTTPStatus.FORBIDDEN
    assert stored_data() == before

    # The product page sets the cookie; base.html sends it as X-CSRFToken.
    client.get(product.get_absolute_url())
    token = client.cookies["csrftoken"].value
    genuine = client.post(url, data, headers={**HTMX, "X-CSRFToken": token})

    assert genuine.status_code == HTTPStatus.OK
    assert genuine.headers.get("HX-Retarget") == "#reviews"


def test_inline_answers_escape_comments_and_name_nobody(
    client, customer, product, delivered_order, order_for
):
    customer.username = "zq-author"
    customer.email = "zq-author@example.com"
    customer.save()
    neighbour = get_user_model().objects.create_user(
        username="zq-neighbour", email="zq-neighbour@example.com"
    )
    order_for(neighbour, Order.Status.DELIVERED, product)
    Review.objects.create(user=neighbour, product=product, rating=5, comment="Fine.")
    client.force_login(customer)

    response = client.post(
        action_url("create", product),
        {"rating": "1", "comment": "<script>alert('x')</script>"},
        headers=HTMX,
    )

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert "<script>alert" not in page
    assert "&lt;script&gt;" in page
    # Only "Verified buyer" — no username or email of anyone.
    assert "zq-" not in page
    assert "Verified buyer" in page


def test_a_plain_success_message_still_appears_once(
    client, customer, product, delivered_order
):
    """Inline answers show the message in the section; a full page leaves
    it to base.html, so it's never said twice."""
    Review.objects.create(user=customer, product=product, rating=3, comment="Old")
    client.force_login(customer)

    response = client.post(
        action_url("edit", product), {"rating": "5", "comment": "New"}, follow=True
    )

    assert response.content.decode().count("Your review has been updated.") == 1


def test_the_page_after_an_inline_action_holds_no_stale_message(
    client, customer, product, delivered_order
):
    """The inline answer showed the message, so the next page doesn't."""
    client.force_login(customer)
    client.post(action_url("create", product), {"rating": "4"}, headers=HTMX)

    page = client.get(product.get_absolute_url()).content.decode()

    assert "Thanks — your review is live." not in page
