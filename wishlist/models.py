from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product


class Wishlist(models.Model):
    """A shopper's private wishlist — one per user, created on first save.

    Only saving creates one: viewing a product (or, later, the wishlist
    page) must never add an empty row.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist",
    )

    def __str__(self):
        return f"Wishlist for {self.user.username}"

    @classmethod
    def for_user(cls, user):
        """Return the user's wishlist, creating it on first touch."""
        wishlist, _ = cls.objects.get_or_create(user=user)
        return wishlist

    @staticmethod
    def has_saved(user, product):
        """Whether ``user`` has saved ``product`` — read-only, never creates."""
        if not user.is_authenticated:
            return False
        return WishlistItem.objects.filter(
            wishlist__user=user, product=product
        ).exists()

    @staticmethod
    def remove_for(user, product):
        """Remove ``product`` from the user's wishlist, if it's there.

        Harmless when it isn't, and never creates a wishlist.
        """
        WishlistItem.objects.filter(wishlist__user=user, product=product).delete()

    def save_product(self, product):
        """Save a product; saving it again keeps the one existing item."""
        item, _ = self.items.get_or_create(product=product)
        return item


class WishlistItem(models.Model):
    """One saved product; the wishlist–product pair is unique."""

    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # default (not auto_now_add) so the seed can fix the demo order.
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-added_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["wishlist", "product"], name="unique_wishlist_product"
            )
        ]

    def __str__(self):
        return self.product.name
