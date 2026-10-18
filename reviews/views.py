"""Review views — thin per the architecture convention.

Every customer URL is the product slug plus ``request.user``; no review
pk ever appears. The rules live on the model and are checked on GET and
POST alike.
"""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from accounts.mixins import StaffRequiredMixin
from products.models import Product

from .forms import HideReviewForm, ReviewForm
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


# --- The back office: moderation ---------------------------------------------
#
# Staff-only, like every back-office screen: anonymous → login, signed-in
# non-staff (a review's own author included) → 403. Hide and restore are
# POST-only views, so a GET is 405, and CSRF middleware guards the POSTs.


class ManageReviewListView(StaffRequiredMixin, ListView):
    """Every review, newest first, 25 a page, filterable via ``?status=``.

    Only the model's own status values filter; anything else shows all.
    A bad ``?page=`` is a 404, as on the other back-office lists.
    """

    template_name = "reviews/manage_reviews.html"
    context_object_name = "reviews"
    paginate_by = 25
    extra_context = {"section": "reviews"}

    def get_queryset(self):
        reviews = Review.objects.select_related("product", "user", "hidden_by")
        if self.active_status():
            reviews = reviews.filter(status=self.active_status())
        return reviews.order_by("-created_at", "-pk")

    def active_status(self):
        status = self.request.GET.get("status", "")
        return status if status in Review.Status.values else ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Review.Status.choices
        context["active_status"] = self.active_status()
        return context


class ManageReviewDetailView(StaffRequiredMixin, DetailView):
    """One review in full, with its moderation controls."""

    template_name = "reviews/manage_review_detail.html"
    context_object_name = "review"
    extra_context = {"section": "reviews"}
    queryset = Review.objects.select_related("product", "user", "hidden_by")

    def get_context_data(self, **kwargs):
        kwargs.setdefault("hide_form", HideReviewForm())
        return super().get_context_data(**kwargs)


class HideReviewView(StaffRequiredMixin, View):
    """POST-only: hide a review, with a reason.

    An invalid reason shows the detail page again with the error. Hiding
    an already-hidden review changes nothing — its original moderator,
    time and reason stand.
    """

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if review.status == Review.Status.HIDDEN:
            return self.already_hidden(review)
        form = HideReviewForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                ManageReviewDetailView.template_name,
                {"review": review, "hide_form": form, "section": "reviews"},
            )
        if not review.hide(request.user, form.cleaned_data["reason"]):
            # Another moderator hid it between our read and our write.
            return self.already_hidden(review)
        messages.success(request, "Review hidden. It no longer appears in the store.")
        return redirect("reviews:manage_review_detail", pk=review.pk)

    def already_hidden(self, review):
        messages.info(
            self.request, "This review is already hidden; nothing was changed."
        )
        return redirect("reviews:manage_review_detail", pk=review.pk)


class RestoreReviewView(StaffRequiredMixin, View):
    """POST-only: publish a hidden review again. Restoring a published
    review changes nothing and says so."""

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if review.restore():
            messages.success(request, "Review restored. It appears in the store again.")
        else:
            messages.info(
                request, "This review is already published; nothing was changed."
            )
        return redirect("reviews:manage_review_detail", pk=review.pk)
