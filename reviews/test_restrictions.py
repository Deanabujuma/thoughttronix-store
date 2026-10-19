from datetime import timedelta
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import DatabaseError, IntegrityError, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from orders.models import Order
from products.models import Product

from .models import Review, ReviewRestriction


def delete_url(product):
    return reverse("reviews:delete", kwargs={"slug": product.slug})


def create_url(product):
    return reverse("reviews:create", kwargs={"slug": product.slug})


@pytest.fixture
def moderator(db):
    return get_user_model().objects.create_user(username="moderator", is_staff=True)


def own_review(customer, product, moderator, status):
    fields = {}
    if status == "hidden":
        fields = {
            "status": Review.Status.HIDDEN,
            "hidden_by": moderator,
            "hidden_at": timezone.now() - timedelta(days=1),
            "hidden_reason": "Off-topic",
        }
    return Review.objects.create(
        user=customer, product=product, rating=1, comment="My words", **fields
    )


# --- Behavior 1: what deleting leaves behind ------------------------------------


@pytest.mark.parametrize(
    "case",
    [
        "hidden",
        "hidden, restriction already there",
        "hidden, deleted twice",
        "published",
    ],
)
def test_deleting_a_hidden_review_leaves_one_restriction_and_a_published_one_none(
    client, customer, product, delivered_order, moderator, staff_user, case
):
    review = own_review(
        customer, product, moderator, "published" if case == "published" else "hidden"
    )
    if case == "hidden, restriction already there":
        ReviewRestriction.objects.create(
            user=customer,
            product=product,
            hidden_reason="An older reason",
            hidden_by=staff_user,
            hidden_at=timezone.now() - timedelta(days=30),
        )
    record = (review.hidden_reason, review.hidden_by, review.hidden_at)
    client.force_login(customer)
    started = timezone.now()

    response = client.post(delete_url(product))

    assert response.status_code == HTTPStatus.FOUND
    assert not Review.objects.filter(pk=review.pk).exists()
    if case == "hidden, deleted twice":
        again = client.post(delete_url(product))
        assert again.status_code == HTTPStatus.NOT_FOUND  # nothing left to delete

    if case == "published":
        assert not ReviewRestriction.objects.exists()
        # Still eligible, so they may write a fresh review straight away.
        assert client.get(create_url(product)).status_code == HTTPStatus.OK
        fresh = client.post(create_url(product), {"rating": "5"})
        assert fresh.status_code == HTTPStatus.FOUND
        assert Review.objects.filter(user=customer, product=product).exists()
        return

    assert ReviewRestriction.objects.count() == 1  # exactly one
    restriction = ReviewRestriction.objects.get()
    assert (restriction.user, restriction.product) == (customer, product)
    assert (
        restriction.hidden_reason,
        restriction.hidden_by,
        restriction.hidden_at,
    ) == record
    assert restriction.created_at >= started
    # It keeps staff's record of the hide, never the review's own words.
    field_names = {f.name for f in ReviewRestriction._meta.get_fields()}
    assert not {"rating", "comment"} & field_names


# --- Guards (normal tests) --------------------------------------------------------


def test_the_database_allows_one_restriction_per_customer_and_product(
    customer, product, moderator
):
    ReviewRestriction.objects.create(
        user=customer, product=product, hidden_reason="Spam", hidden_at=timezone.now()
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ReviewRestriction.objects.create(
            user=customer,
            product=product,
            hidden_reason="Again",
            hidden_at=timezone.now(),
        )


def test_a_failed_delete_leaves_neither_a_restriction_nor_a_missing_review(
    customer, product, moderator, monkeypatch
):
    """The restriction and the deletion happen together or not at all."""
    review = own_review(customer, product, moderator, "hidden")

    def broken_delete(self, *args, **kwargs):
        raise DatabaseError("the delete failed")

    monkeypatch.setattr(Review, "delete", broken_delete)

    with pytest.raises(DatabaseError):
        review.delete_by_author()

    assert Review.objects.filter(pk=review.pk).exists()
    assert not ReviewRestriction.objects.exists()


# --- Behavior 2: a restriction blocks that product only -----------------------

RESTRICTED = (
    "You cannot currently review this product. If you believe this is a "
    "mistake, please contact our team."
)


def test_a_restriction_blocks_reviewing_that_product_only(
    client, customer, product, category, order_for, moderator
):
    other = Product.objects.create(
        name="Seraphine Mini",
        slug="seraphine-mini",
        price=Decimal("99.00"),
        category=category,
    )
    # Received both, so without the restriction both could be reviewed.
    order_for(customer, Order.Status.DELIVERED, product, other)
    ReviewRestriction.objects.create(
        user=customer,
        product=product,
        hidden_reason="Off-topic",
        hidden_by=moderator,
        hidden_at=timezone.now(),
    )
    client.force_login(customer)
    write = f'href="{create_url(product)}"'

    # The restricted product: refused on GET and POST, and nothing is saved.
    assert client.get(create_url(product)).status_code == HTTPStatus.FORBIDDEN
    posted = client.post(create_url(product), {"rating": "5", "comment": "Again"})
    assert posted.status_code == HTTPStatus.FORBIDDEN
    assert not Review.objects.filter(product=product).exists()
    # Its page explains, in place of the button.
    page = client.get(product.get_absolute_url()).content.decode()
    assert RESTRICTED in page
    assert write not in page and "Write a review" not in page

    # The other product they received is unaffected.
    other_page = client.get(other.get_absolute_url()).content.decode()
    assert f'href="{create_url(other)}"' in other_page
    assert RESTRICTED not in other_page
    assert client.get(create_url(other)).status_code == HTTPStatus.OK
    created = client.post(create_url(other), {"rating": "4"})
    assert created.status_code == HTTPStatus.FOUND
    assert Review.objects.filter(user=customer, product=other).exists()


# --- Behavior 3: clearing a restriction ---------------------------------------

CLEARED = "Restriction cleared. customer can review Seraphine Home Hub again."
ALREADY_CLEARED = "This restriction was already cleared; nothing was changed."
CASES = [
    ("anonymous", "get", "login"),
    ("anonymous", "post", "login"),
    ("restricted customer", "get", HTTPStatus.FORBIDDEN),
    ("restricted customer", "post", HTTPStatus.FORBIDDEN),
    ("another customer", "get", HTTPStatus.FORBIDDEN),
    ("another customer", "post", HTTPStatus.FORBIDDEN),
    ("staff without CSRF", "post", HTTPStatus.FORBIDDEN),
    ("staff", "get", "confirmation"),
    ("staff", "post", "cleared"),
    ("staff", "post twice", "already cleared"),
]


@pytest.mark.parametrize(
    ("who", "method", "expected"),
    CASES,
    ids=[f"{who}-{method}" for who, method, _ in CASES],
)
def test_only_staff_can_clear_a_restriction_and_only_by_a_confirmed_post(
    customer,
    other_customer,
    staff_user,
    product,
    delivered_order,
    moderator,
    who,
    method,
    expected,
):
    restriction = ReviewRestriction.objects.create(
        user=customer,
        product=product,
        hidden_reason="Off-topic",
        hidden_by=moderator,
        hidden_at=timezone.now(),
    )
    url = reverse("reviews:manage_restriction_clear", kwargs={"pk": restriction.pk})
    restrictions = reverse("reviews:manage_restrictions")
    client = Client(enforce_csrf_checks=(who == "staff without CSRF"))
    signed_in = {
        "restricted customer": customer,
        "another customer": other_customer,
        "staff": staff_user,
        "staff without CSRF": staff_user,
    }
    if who in signed_in:
        client.force_login(signed_in[who])

    if method == "post twice":
        client.post(url)
        response = client.post(url)
    else:
        response = getattr(client, method)(url)

    still_there = ReviewRestriction.objects.filter(pk=restriction.pk).exists()
    if expected == "login":
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == f"{reverse('accounts:login')}?next={url}"
        assert still_there
    elif expected == "confirmation":
        # Names who and what; opening it changes nothing.
        page = response.content.decode()
        assert response.status_code == HTTPStatus.OK
        assert "customer" in page and product.name in page
        assert 'method="post"' in page and "csrfmiddlewaretoken" in page
        assert still_there
    elif expected in ("cleared", "already cleared"):
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == restrictions
        message = CLEARED if expected == "cleared" else ALREADY_CLEARED
        assert message in [str(m) for m in get_messages(response.wsgi_request)]
        assert not still_there
        # Eligible again: the customer is offered the form and can post.
        shopper = Client()
        shopper.force_login(customer)
        page = shopper.get(product.get_absolute_url()).content.decode()
        assert f'href="{create_url(product)}"' in page
        assert shopper.post(create_url(product), {"rating": "4"}).status_code == (
            HTTPStatus.FOUND
        )
        assert Review.objects.filter(user=customer, product=product).exists()
    else:
        assert response.status_code == expected
        assert still_there


# --- The Restrictions page (normal tests) ---------------------------------------

RESTRICTIONS = reverse("reviews:manage_restrictions")


def restrict(user, product, moderator, *, days_ago=0):
    return ReviewRestriction.objects.create(
        user=user,
        product=product,
        hidden_reason="Off-topic",
        hidden_by=moderator,
        hidden_at=timezone.now() - timedelta(days=days_ago + 1),
        created_at=timezone.now() - timedelta(days=days_ago),
    )


@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client


@pytest.mark.parametrize("who", ["anonymous", "customer"])
def test_the_restrictions_page_is_staff_only(client, customer, who):
    if who == "customer":
        client.force_login(customer)

    response = client.get(RESTRICTIONS)

    if who == "anonymous":
        assert response.url == f"{reverse('accounts:login')}?next={RESTRICTIONS}"
    else:
        assert response.status_code == HTTPStatus.FORBIDDEN


def test_the_restrictions_page_shows_each_restrictions_columns(
    staff_client, customer, product, moderator
):
    restriction = restrict(customer, product, moderator)

    page = staff_client.get(RESTRICTIONS).content.decode()

    assert "1 active restriction" in page
    assert ">customer<" in page
    assert f'href="{product.get_absolute_url()}"' in page and product.name in page
    assert "Off-topic" in page
    assert ">moderator<" in page
    clear = reverse("reviews:manage_restriction_clear", kwargs={"pk": restriction.pk})
    assert f'href="{clear}"' in page and "Clear restriction" in page


def test_the_restrictions_page_shows_25_a_page_newest_first(
    staff_client, product, moderator
):
    for n in range(26):
        user = get_user_model().objects.create_user(username=f"restricted{n:02}")
        restrict(user, product, moderator, days_ago=n)

    first = staff_client.get(RESTRICTIONS)
    second = staff_client.get(RESTRICTIONS, {"page": 2})

    names = [r.user.username for r in first.context["restrictions"]]
    assert names == [f"restricted{n:02}" for n in range(25)]
    assert [r.user.username for r in second.context["restrictions"]] == ["restricted25"]


def test_a_deleted_moderator_leaves_the_restriction_active_as_former_staff(
    staff_client, customer, product, moderator
):
    restriction = restrict(customer, product, moderator)
    moderator.delete()

    restriction.refresh_from_db()
    assert restriction.hidden_by is None
    assert ReviewRestriction.applies(customer, product)  # still active
    assert "Former staff member" in staff_client.get(RESTRICTIONS).content.decode()


def test_the_restrictions_page_has_a_designed_empty_state(staff_client):
    page = staff_client.get(RESTRICTIONS).content.decode()

    assert "No active restrictions" in page


def test_the_reviews_list_links_to_the_restrictions_page(staff_client):
    page = staff_client.get(reverse("reviews:manage_reviews")).content.decode()

    assert f'href="{RESTRICTIONS}"' in page


def test_clearing_one_restriction_leaves_every_other_alone(
    staff_client, customer, other_customer, product, unavailable_product, moderator
):
    target = restrict(customer, product, moderator)
    same_customer = restrict(customer, unavailable_product, moderator)
    same_product = restrict(other_customer, product, moderator)

    staff_client.post(
        reverse("reviews:manage_restriction_clear", kwargs={"pk": target.pk})
    )

    remaining = set(ReviewRestriction.objects.values_list("pk", flat=True))
    assert remaining == {same_customer.pk, same_product.pk}


def test_a_made_up_restriction_id_redirects_with_the_info_message(staff_client):
    url = reverse("reviews:manage_restriction_clear", kwargs={"pk": 999})

    for response in [staff_client.get(url), staff_client.post(url)]:
        assert response.url == RESTRICTIONS
        # The GET's unread message is still queued when the POST runs.
        assert "This restriction was already cleared; nothing was changed." in [
            str(m) for m in get_messages(response.wsgi_request)
        ]


def test_a_restricted_customer_who_is_no_longer_eligible_sees_the_restriction(
    client, customer, product, delivered_order, moderator
):
    """The more specific reason wins over "only customers who've received"."""
    restrict(customer, product, moderator)
    delivered_order.status = Order.Status.CANCELLED
    delivered_order.save()
    client.force_login(customer)

    page = client.get(product.get_absolute_url()).content.decode()

    assert RESTRICTED in page
    assert "Only customers who've received" not in page


def test_restricted_staff_see_no_restriction_message(
    client, customer, product, delivered_order, moderator
):
    restrict(customer, product, moderator)
    customer.is_staff = True
    customer.save()
    client.force_login(customer)

    assert RESTRICTED not in client.get(product.get_absolute_url()).content.decode()


# --- Cascades ---------------------------------------------------------------------


def test_deleting_a_product_removes_its_reviews_and_restrictions(
    customer, other_customer, product, moderator
):
    Review.objects.create(user=other_customer, product=product, rating=4)
    restrict(customer, product, moderator)

    product.delete()

    assert not Review.objects.exists()
    assert not ReviewRestriction.objects.exists()


def test_deleting_a_customer_removes_their_reviews_and_restrictions(
    customer, product, unavailable_product, moderator
):
    Review.objects.create(user=customer, product=product, rating=4)
    restrict(customer, unavailable_product, moderator)

    customer.delete()

    assert not Review.objects.exists()
    assert not ReviewRestriction.objects.exists()
