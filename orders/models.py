from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from functools import cached_property

from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone
from django.utils.dateformat import format as format_date

from products.models import Product

ZERO = Decimal("0.00")

CENT = Decimal("0.01")

coupon_code_validator = RegexValidator(
    r"^[A-Za-z0-9-]{3,30}$",
    "Use 3–30 letters, digits, or hyphens.",
)


class InvalidCouponError(ValueError):
    """A discount code that can't be applied; the message is customer-facing."""


class CouponQuerySet(models.QuerySet):
    """Status filters share one precedence: retired, then expired, then live."""

    def live(self):
        return self.filter(is_active=True, expires_on__gte=timezone.localdate())

    def expired(self):
        return self.filter(is_active=True, expires_on__lt=timezone.localdate())

    def retired(self):
        return self.filter(is_active=False)

    def with_status(self, status):
        """Narrow to one ``Coupon.Status``; anything else means all codes."""
        return {
            Coupon.Status.LIVE: self.live,
            Coupon.Status.EXPIRED: self.expired,
            Coupon.Status.RETIRED: self.retired,
        }.get(status, self.all)()

    def with_use_count(self):
        """Annotate ``use_count``: every order that used the code, cancelled too."""
        return self.annotate(use_count=models.Count("orders", distinct=True))

    def redeem(self, code, cart):
        """The one validator: return the coupon for ``code``, or raise.

        Checks run in a fixed order — unknown, retired, expired, then no
        eligible product in the cart — so each failure has exactly one
        message. Raises ``InvalidCouponError``.
        """
        code = Coupon.normalize_code(code)
        try:
            coupon = self.get(code=code)
        except Coupon.DoesNotExist:
            raise InvalidCouponError(f"We don't recognize the code {code}.") from None
        if not coupon.is_active:
            raise InvalidCouponError(f"{code} is no longer available.")
        if coupon.expires_on < timezone.localdate():
            raise InvalidCouponError(
                f"{code} expired on {format_date(coupon.expires_on, 'M j, Y')}."
            )
        if coupon.applies_to == Coupon.AppliesTo.PRODUCTS and not any(
            coupon.covers(item.product) for item in cart.lines()
        ):
            names = list(coupon.products.values_list("name", flat=True))
            where = "which isn't" if len(names) == 1 else "none of which are"
            raise InvalidCouponError(
                f"{code} applies to {_name_list(names)}, {where} in your cart."
            )
        return coupon


def _name_list(names, shown=3):
    """Join names for a message: "A and B", or "A, B, C and 4 more"."""
    if len(names) > shown:
        return f"{', '.join(names[:shown])} and {len(names) - shown} more"
    if len(names) > 1:
        return f"{', '.join(names[:-1])} and {names[-1]}"
    return names[0]


class Coupon(models.Model):
    """A percentage discount code — "Discount code" to the people using it.

    Orders snapshot what a code gave them, so editing or retiring a code
    never changes a past order.
    """

    class AppliesTo(models.TextChoices):
        ORDER = "ORDER", "Whole order"
        PRODUCTS = "PRODUCTS", "Selected products"

    class Status(models.TextChoices):
        LIVE = "live", "Live"
        EXPIRED = "expired", "Expired"
        RETIRED = "retired", "Retired"

    code = models.CharField(
        max_length=30, unique=True, validators=[coupon_code_validator]
    )
    percent_off = models.PositiveSmallIntegerField(
        "percent off", validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    applies_to = models.CharField(
        max_length=10, choices=AppliesTo.choices, default=AppliesTo.ORDER
    )
    products = models.ManyToManyField(Product, blank=True, related_name="coupons")
    expires_on = models.DateField("valid through")
    is_active = models.BooleanField("active", default=True)
    created_at = models.DateTimeField(default=timezone.now)

    objects = CouponQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.normalize_code(self.code)
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_code(code):
        """The canonical form of a code: trimmed and uppercased."""
        return code.strip().upper()

    @property
    def status(self):
        if not self.is_active:
            return self.Status.RETIRED
        if self.expires_on < timezone.localdate():
            return self.Status.EXPIRED
        return self.Status.LIVE

    @property
    def is_used(self):
        """True once any order — cancelled included — has used the code."""
        return self.orders.exists()

    @cached_property
    def eligible_product_ids(self):
        return frozenset(self.products.values_list("pk", flat=True))

    def covers(self, product):
        """Whether ``product``'s lines are eligible for this code."""
        if self.applies_to == self.AppliesTo.ORDER:
            return True
        return product.pk in self.eligible_product_ids

    def discount_for(self, product, unit_price, quantity):
        """This code's discount on one line, rounded half-up to the cent.

        Zero when the line isn't eligible. An order's discount is the sum
        of its line discounts, so line and order figures always agree.
        """
        if not self.covers(product):
            return ZERO
        line_total = unit_price * quantity
        return (line_total * self.percent_off / 100).quantize(
            CENT, rounding=ROUND_HALF_UP
        )


@dataclass
class PricedLine:
    """One cart line priced under a coupon (or none)."""

    product: Product
    quantity: int
    unit_price: Decimal
    discount: Decimal

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def net_total(self):
        return self.line_total - self.discount


@dataclass
class CartPricing:
    """What the cart costs under a coupon — shared by the checkout preview
    and ``place_order``, so the preview is exactly what gets charged."""

    lines: list[PricedLine]
    coupon: "Coupon | None"

    @property
    def subtotal(self):
        return sum((line.line_total for line in self.lines), ZERO)

    @property
    def discount(self):
        return sum((line.discount for line in self.lines), ZERO)

    @property
    def total(self):
        return self.subtotal - self.discount


class Cart(models.Model):
    """A customer's cart — one per user, created lazily on first touch."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )

    def __str__(self):
        return f"Cart for {self.user.username}"

    @classmethod
    def for_user(cls, user):
        """Return the user's cart, creating it on first touch."""
        cart, _ = cls.objects.get_or_create(user=user)
        return cart

    def add(self, product):
        """Add a product to the cart; a duplicate add increments its line."""
        item, created = self.items.get_or_create(product=product)
        if not created:
            item.quantity += 1
            item.save()
        return item

    def lines(self):
        """Line items with their products loaded, ready for display."""
        return self.items.select_related("product")

    def total(self):
        return sum((item.line_total for item in self.lines()), ZERO)

    def priced(self, coupon=None):
        """Price every line at the current catalog price under ``coupon``."""
        return CartPricing(
            lines=[
                PricedLine(
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                    discount=(
                        coupon.discount_for(
                            item.product, item.product.price, item.quantity
                        )
                        if coupon
                        else ZERO
                    ),
                )
                for item in self.lines()
            ],
            coupon=coupon,
        )

    def item_count(self):
        """Total units across all lines — the navbar badge number."""
        return self.items.aggregate(count=models.Sum("quantity"))["count"] or 0


class CartItem(models.Model):
    """One product line in a cart; the cart–product pair is unique."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_cart_product"
            )
        ]

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    @property
    def line_total(self):
        return self.product.price * self.quantity

    def increment(self):
        self.quantity += 1
        self.save()

    def decrement(self):
        """Step the quantity down, stopping at one — removal is explicit."""
        if self.quantity > 1:
            self.quantity -= 1
            self.save()


class Order(models.Model):
    """A placed order — a snapshot, never a live view of the catalog.

    Addresses are flat denormalized fields: the order must not change if
    the customer later edits anything. Of the card, only the last four
    digits survive checkout. A discount is snapshotted the same way —
    ``total`` is what the customer paid; the ``coupon`` link is only for
    the back office, and PROTECT means a used code can never be deleted.
    """

    class Status(models.TextChoices):
        PLACED = "PLACED", "Placed"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PLACED
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    email = models.EmailField()

    shipping_name = models.CharField(max_length=100)
    shipping_street = models.CharField(max_length=200)
    shipping_line2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=2)
    shipping_zip = models.CharField(max_length=10)

    billing_name = models.CharField(max_length=100)
    billing_street = models.CharField(max_length=200)
    billing_line2 = models.CharField(max_length=200, blank=True)
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=2)
    billing_zip = models.CharField(max_length=10)

    card_last4 = models.CharField(max_length=4)

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders",
    )
    discount_code = models.CharField(max_length=30, blank=True)
    discount_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)

    # default (not auto_now_add) so the seed can backdate orders.
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.number

    @property
    def number(self):
        """The customer-facing order number, e.g. ``TT-2026-00042``."""
        return f"TT-{self.created_at.year}-{self.pk:05d}"

    @property
    def subtotal(self):
        """The order before its discount."""
        return self.total + self.discount_amount


class OrderItem(models.Model):
    """One line of an order, priced as of purchase time.

    Name and unit price are denormalized: order history must not change
    when the catalog does. The product FK survives for linking while the
    product exists.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

    @property
    def line_total(self):
        """The line before any discount."""
        return self.unit_price * self.quantity

    @property
    def net_total(self):
        """What the customer paid for the line."""
        return self.line_total - self.discount_amount
