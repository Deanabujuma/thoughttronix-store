"""A characterization test: the seed's existing demo world, pinned.

Written and passing *before* reviews were added to the seed (Phase 6 of
the product-reviews plan). It snapshots everything the seed already
built — orders and their lines, discount codes, the customer's cart,
wishlist and addresses, the demo accounts — plus the dashboard figures,
all at one frozen clock. Adding reviews must leave every byte of it
alone: the review RNG and code may not shift a single existing draw.

It runs only in pytest's isolated database, never against db.sqlite3.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from accounts.models import Address
from dashboard import queries
from orders.models import Cart, Coupon, Order
from wishlist.models import WishlistItem

# The seed dates everything relative to "now"; freezing it makes the
# demo world byte-for-byte reproducible.
FROZEN_NOW = datetime(2026, 10, 18, 17, 0, tzinfo=UTC)


@pytest.fixture
def frozen_clock(monkeypatch):
    monkeypatch.setattr(timezone, "now", lambda: FROZEN_NOW)
    return FROZEN_NOW


def demo_world():
    """Everything the seed built before reviews, by natural keys only."""
    orders = [
        {
            "user": order.user.username,
            "status": order.status,
            "total": order.total,
            "discount": [
                order.discount_code,
                order.discount_percent,
                order.discount_amount,
            ],
            "created_at": order.created_at,
            "email": order.email,
            "card_last4": order.card_last4,
            "shipping": [
                order.shipping_name,
                order.shipping_street,
                order.shipping_city,
                order.shipping_state,
                order.shipping_zip,
            ],
            "lines": [
                [
                    item.product.slug if item.product else None,
                    item.product_name,
                    item.unit_price,
                    item.quantity,
                    item.discount_amount,
                ]
                for item in order.items.select_related("product")
            ],
        }
        for order in Order.objects.select_related("user").order_by(
            "created_at", "user__username", "total"
        )
    ]
    coupons = [
        [
            c.code,
            c.percent_off,
            c.applies_to,
            c.expires_on,
            c.is_active,
            c.created_at,
            sorted(c.products.values_list("slug", flat=True)),
        ]
        for c in Coupon.objects.order_by("code")
    ]
    customer = get_user_model().objects.get(username="customer")
    cart = sorted(
        [item.product.slug, item.quantity]
        for item in Cart.for_user(customer).items.select_related("product")
    )
    wishlist = [
        [item.product.slug, item.added_at]
        for item in WishlistItem.objects.filter(wishlist__user=customer).select_related(
            "product"
        )
    ]
    addresses = [
        [
            a.label,
            a.name,
            a.street,
            a.line2,
            a.city,
            a.state,
            a.zip_code,
            a.is_default_shipping,
            a.is_default_billing,
        ]
        for a in Address.objects.filter(user=customer).order_by("label")
    ]
    users = [
        [u.username, u.email, u.is_staff, u.is_superuser, u.job_title]
        for u in get_user_model().objects.order_by("username")
    ]
    month_ago = FROZEN_NOW - timedelta(days=30)
    dashboard = {
        "total_revenue": queries.total_revenue(),
        "order_count": queries.order_count(),
        "average_order_value": queries.average_order_value(),
        "revenue_by_month": queries.revenue_over_time(bucket="month"),
        "revenue_last_30_days": queries.revenue_over_time(month_ago, bucket="day"),
        "top_products": queries.top_products(),
        "order_count_last_30_days": queries.order_count(month_ago),
    }
    return {
        "orders": orders,
        "coupons": coupons,
        "cart": cart,
        "wishlist": wishlist,
        "addresses": addresses,
        "users": users,
        "dashboard": dashboard,
    }


def digest(world):
    """A SHA-256 of the canonical JSON — any change at all changes it."""
    text = json.dumps(world, sort_keys=True, default=str)
    return hashlib.sha256(text.encode()).hexdigest()


# Recorded from the seed as it stood before reviews were added (commit
# 4fe2b56), at FROZEN_NOW. If this ever has to change, the change to the
# existing demo world must be deliberate and reviewed — never a side
# effect of adding something else.
BASELINE_DIGEST = "7d389c6263c13a71d6451a6be34a877aa58ec7c17f80d5a65f14a7ee4bfba774"


def test_the_seed_still_builds_the_same_demo_world(db, frozen_clock):
    call_command("seed")

    world = demo_world()

    # Readable landmarks first, so a failure says roughly what moved.
    statuses = {}
    for order in world["orders"]:
        statuses[order["status"]] = statuses.get(order["status"], 0) + 1
    assert statuses == {"CANCELLED": 5, "DELIVERED": 42, "PLACED": 1, "SHIPPED": 4}
    assert sum(len(order["lines"]) for order in world["orders"]) == 109
    assert [c[0] for c in world["coupons"]] == [
        "HUB15",
        "LAUNCH25",
        "SUMMER20",
        "THOUGHTS10",
    ]
    assert len(world["users"]) == 12
    dashboard = world["dashboard"]
    assert dashboard["order_count"] == 47
    assert f"{dashboard['total_revenue']:.2f}" == "57395.20"
    assert dashboard["average_order_value"] == Decimal("1221.17")
    assert dashboard["order_count_last_30_days"] == 11
    assert [p["product_name"] for p in dashboard["top_products"]] == [
        "MindSync Family",
        "RecallPro",
        "MindSync",
        "MindSync Duo",
        "MoodSet",
    ]
    # Then every byte of it.
    assert digest(world) == BASELINE_DIGEST
