"""Wishlist views — thin per the architecture convention.

Save and remove are HTMX actions from the product detail page: each acts
on the signed-in user's own wishlist, then re-renders the button partial
with the true saved state. The partial replaces only itself.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import ListView

from products.models import Product

from .models import Wishlist, WishlistItem


class WishlistView(LoginRequiredMixin, ListView):
    """The shopper's wishlist page — only their own items, newest first.

    Read-only: it never creates a wishlist, so a user who has never saved
    anything sees the empty state. Removing happens on the detail page.
    """

    template_name = "wishlist/list.html"
    context_object_name = "items"

    def get_queryset(self):
        # The category is loaded too: a product without an image shows
        # its category's placeholder.
        return WishlistItem.objects.filter(
            wishlist__user=self.request.user
        ).select_related("product__category")


class WishlistActionView(LoginRequiredMixin, View):
    """Base for the button's actions: act, then re-render the button.

    ``pk`` is the product's. Every change goes through ``request.user``,
    so no request can touch another user's wishlist.
    """

    http_method_names = ["post"]
    products = Product.objects.all()

    def post(self, request, pk):
        product = get_object_or_404(self.products, pk=pk)
        self.act(request.user, product)
        return render(
            request,
            "wishlist/partials/_wishlist_button.html",
            {"product": product, "saved": Wishlist.has_saved(request.user, product)},
        )

    def act(self, user, product):
        raise NotImplementedError


class SaveToWishlistView(WishlistActionView):
    """Save only what's for sale — an unavailable product 404s, like the cart."""

    products = Product.objects.available()

    def act(self, user, product):
        Wishlist.for_user(user).save_product(product)


class RemoveFromWishlistView(WishlistActionView):
    """Remove from all products, so an unavailable one can still go."""

    def act(self, user, product):
        Wishlist.remove_for(user, product)
