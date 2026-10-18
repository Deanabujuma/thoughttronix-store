"""Review views — thin per the architecture convention.

Every customer URL is the product slug plus ``request.user``; no review
pk ever appears. The rules live on the model and are checked on GET and
POST alike.
"""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView

from products.models import Product

from .forms import ReviewForm
from .models import Review


class ReviewCreateView(UserPassesTestMixin, CreateView):
    """Write a review. Anonymous → login; signed in but not allowed → 403.

    A customer who already has a review — a double click, a second tab —
    is sent back to the product with a message instead, and never gets a
    second row or an error page.
    """

    form_class = ReviewForm
    template_name = "reviews/review_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs["slug"])
        if Review.objects.own(request.user, self.product):
            return self.already_reviewed()
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return Review.objects.can_create(self.request.user, self.product)

    def get_context_data(self, **kwargs):
        return super().get_context_data(product=self.product, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.product = self.product
        # Two requests can both pass the check before either saves; the
        # unique constraint lets only one in. The savepoint keeps the
        # loser's failed insert from breaking the rest of the request.
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            # Only the duplicate is expected — anything else re-raises.
            if not Review.objects.own(self.request.user, self.product):
                raise
            return self.already_reviewed()
        messages.success(self.request, "Thanks — your review is live.")
        return response

    def already_reviewed(self):
        messages.info(self.request, "You've already reviewed this product.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return f"{self.product.get_absolute_url()}#reviews"
