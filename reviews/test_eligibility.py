import pytest
from django.contrib.auth.models import AnonymousUser

from orders.models import Order
from products.models import Product

from .models import Review

Status = Order.Status


@pytest.mark.parametrize(
    ("status", "role", "bought", "expected"),
    [
        (Status.DELIVERED, "customer", "this product", True),
        (Status.PLACED, "customer", "this product", False),
        (Status.SHIPPED, "customer", "this product", False),
        (Status.CANCELLED, "customer", "this product", False),
        (Status.DELIVERED, "staff", "this product", False),
        (Status.DELIVERED, "superuser", "this product", False),
        (Status.DELIVERED, "customer", "a same-named product", False),
    ],
)
def test_only_a_delivered_order_of_this_product_lets_a_regular_customer_review(
    customer, product, order_for, status, role, bought, expected
):
    customer.is_staff = role == "staff"
    customer.is_superuser = role == "superuser"
    customer.save()
    if bought == "this product":
        purchased = product
    else:
        # Same name, different record: matching is by FK, never by name.
        purchased = Product.objects.create(
            name=product.name,
            slug="seraphine-home-hub-refurbished",
            price=product.price,
            category=product.category,
        )
    order_for(customer, status, purchased)

    assert Review.objects.can_create(customer, product) is expected


def test_an_anonymous_visitor_cannot_review(product):
    assert Review.objects.can_create(AnonymousUser(), product) is False


def test_an_existing_review_blocks_a_second_one(customer, product, delivered_order):
    Review.objects.create(user=customer, product=product, rating=4)

    assert Review.objects.can_create(customer, product) is False


def test_a_review_of_one_product_does_not_block_another(
    customer, product, unavailable_product, order_for
):
    """It also shows availability doesn't matter: EchoPatch isn't for sale."""
    order_for(customer, Status.DELIVERED, product, unavailable_product)
    Review.objects.create(user=customer, product=product, rating=4)

    assert Review.objects.can_create(customer, unavailable_product) is True


# --- Editing and deleting -----------------------------------------------------


def test_the_author_may_edit_while_still_eligible(customer, product, delivered_order):
    review = Review.objects.create(user=customer, product=product, rating=4)

    assert review.can_edit(customer) is True
    assert review.can_delete(customer) is True


@pytest.mark.parametrize(
    "status", [Status.PLACED, Status.SHIPPED, Status.CANCELLED], ids=str.lower
)
def test_an_author_whose_order_changes_may_delete_but_not_edit(
    customer, product, delivered_order, status
):
    review = Review.objects.create(user=customer, product=product, rating=4)
    delivered_order.status = status
    delivered_order.save()

    review.refresh_from_db()
    assert review.status == Review.Status.PUBLISHED  # the review is untouched
    assert review.can_edit(customer) is False
    assert review.can_delete(customer) is True


def test_a_delivered_order_of_another_product_does_not_keep_edit_rights(
    customer, product, unavailable_product, order_for
):
    review = Review.objects.create(user=customer, product=product, rating=4)
    order_for(customer, Status.DELIVERED, unavailable_product)

    assert review.can_edit(customer) is False


def test_a_superuser_author_may_delete_but_not_edit(customer, product, delivered_order):
    review = Review.objects.create(user=customer, product=product, rating=4)
    customer.is_superuser = True
    customer.save()

    assert review.can_edit(customer) is False
    assert review.can_delete(customer) is True


def test_nobody_else_may_edit_or_delete_a_review(
    customer, other_customer, staff_user, product, delivered_order, order_for
):
    review = Review.objects.create(user=customer, product=product, rating=4)
    order_for(other_customer, Status.DELIVERED, product)  # eligible, not the author

    for user in [other_customer, staff_user, AnonymousUser()]:
        assert review.can_edit(user) is False
        assert review.can_delete(user) is False
