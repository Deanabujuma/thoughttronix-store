"""Project-wide pytest fixtures.

Shared test data lives here as plain fixtures — no factories. The suite
grows with the project; tests never invoke the seed command.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Address
from orders.models import Cart, CartItem, Coupon
from products.models import Category, Product, Tag


@pytest.fixture
def customer(db):
    return get_user_model().objects.create_user(
        username="customer", password="customer123"
    )


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username="employee",
        password="employee123",
        is_staff=True,
        job_title="Junior Thought Curator",
    )


@pytest.fixture
def address(customer):
    """The customer's first saved address — so both of their defaults."""
    return Address.objects.create(
        user=customer,
        label="Home",
        name="Casey Monroe",
        street="214 Synapse Street",
        city="Canyon",
        state="TX",
        zip_code="79015",
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name="Home Assistants", slug="home-assistants")


@pytest.fixture
def product(category):
    return Product.objects.create(
        name="Seraphine Home Hub",
        slug="seraphine-home-hub",
        tagline="She's always listening. In a good way.",
        description="The flagship Seraphine hub with a seven-microphone array.",
        price=Decimal("349.99"),
        category=category,
    )


@pytest.fixture
def unavailable_product(category):
    return Product.objects.create(
        name="EchoPatch",
        slug="echopatch",
        tagline="Never miss a word. Anyone's.",
        price=Decimal("139.00"),
        is_available=False,
        category=category,
    )


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="bestseller", slug="bestseller")


@pytest.fixture
def cart(customer):
    return Cart.for_user(customer)


@pytest.fixture
def cart_item(cart, product):
    return CartItem.objects.create(cart=cart, product=product, quantity=2)


# Discount codes are dated relative to the store's own today, so the
# expiry rules hold whenever the suite runs — no clock freezing needed.


@pytest.fixture
def whole_order_coupon(db):
    return Coupon.objects.create(
        code="THOUGHTS10",
        percent_off=10,
        expires_on=timezone.localdate() + timedelta(days=30),
    )


@pytest.fixture
def product_coupon(product):
    coupon = Coupon.objects.create(
        code="HUB15",
        percent_off=15,
        applies_to=Coupon.AppliesTo.PRODUCTS,
        expires_on=timezone.localdate() + timedelta(days=30),
    )
    coupon.products.add(product)
    return coupon


@pytest.fixture
def expired_coupon(db):
    return Coupon.objects.create(
        code="SUMMER20",
        percent_off=20,
        expires_on=timezone.localdate() - timedelta(days=1),
    )


@pytest.fixture
def retired_coupon(db):
    return Coupon.objects.create(
        code="LAUNCH25",
        percent_off=25,
        expires_on=timezone.localdate() + timedelta(days=30),
        is_active=False,
    )
