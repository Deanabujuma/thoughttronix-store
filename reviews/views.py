"""Review views — thin per the architecture convention.

Every customer URL is the product slug plus ``request.user``; no review
pk ever appears. The rules live on the model and are checked on GET and
POST alike.
"""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DeleteView, UpdateView

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


class OwnReviewMixin(UserPassesTestMixin):
    """Acts on ``request.user``'s own review of the product in the URL.

    The URL names the product, never the review, so no request can reach
    anyone else's. In order: anonymous → login; no review of your own →
    404 (another customer's review of the product is never looked at);
    your review, but not allowed → 403. Subclasses supply ``allows``.
    """

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs["slug"])
        self.review = Review.objects.own(request.user, self.product)
        if request.user.is_authenticated and self.review is None:
            raise Http404("You have no review of this product.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.review

    def test_func(self):
        return self.review is not None and self.allows(self.review)

    def allows(self, review):
        raise NotImplementedError

    def get_success_url(self):
        return f"{self.product.get_absolute_url()}#reviews"


class ReviewUpdateView(OwnReviewMixin, UpdateView):
    """Edit your own review, while ``can_edit`` allows it."""

    form_class = ReviewForm
    template_name = "reviews/review_form.html"

    def allows(self, review):
        return review.can_edit(self.request.user)

    def get_context_data(self, **kwargs):
        return super().get_context_data(product=self.product, editing=True, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your review has been updated.")
        return response


class ReviewDeleteView(OwnReviewMixin, DeleteView):
    """Delete your own review: GET shows a confirmation and changes
    nothing; only the POST deletes, through ``delete_by_author``."""

    template_name = "reviews/review_confirm_delete.html"

    def allows(self, review):
        return review.can_delete(self.request.user)

    def get_context_data(self, **kwargs):
        return super().get_context_data(product=self.product, **kwargs)

    def form_valid(self, form):
        self.object.delete_by_author()
        messages.success(self.request, "Your review has been deleted.")
        return redirect(self.get_success_url())
