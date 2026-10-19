"""Review views — thin per the architecture convention.

Every customer URL is the product slug plus ``request.user``; no review
pk ever appears. The rules live on the model and are checked on GET and
POST alike.
"""

from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.vary import vary_on_headers
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
from .models import Review, ReviewRestriction

REVIEWS_PER_PAGE = 10


def reviews_section_context(request, product):
    """Everything the product page's ``#reviews`` section needs.

    One source for the detail page and the inline HTMX responses, so the
    section reads the same however it's rendered. The visitor's own
    review is pinned on its own, so it's left out of the public list.
    """
    user = request.user
    own_review = Review.objects.own(user, product)
    reviews = (
        Review.objects.published()
        .filter(product=product)
        .order_by("-created_at", "-pk")
    )
    if own_review:
        reviews = reviews.exclude(pk=own_review.pk)
    # Paged on ?reviews=N, so the catalog's own ?page=N never collides.
    # get_page never errors: not a number → page 1; out of range
    # (0 and negatives too) → the last page.
    review_page = Paginator(reviews, REVIEWS_PER_PAGE).get_page(
        request.GET.get("reviews", 1)
    )
    return {
        "rating": Review.objects.summary_for(product),
        "own_review": own_review,
        # The author may always delete; Edit shows only while allowed.
        "can_edit_review": bool(own_review and own_review.can_edit(user)),
        "review_state": Review.objects.visitor_state(user, product, own_review),
        "reviews": review_page,
    }


def is_htmx(request):
    """Whether HTMX sent this request — the product page's inline actions."""
    return request.headers.get("HX-Request") == "true"


def refreshing(response):
    """Tell HTMX to reload the page. It doesn't swap an error response, so
    a refused inline action reloads the page into its true state."""
    response["HX-Refresh"] = "true"
    return response


class ReviewActionMixin:
    """How a review action answers HTMX — after success, and when refused.

    Success: an inline request gets the re-rendered ``#reviews`` section,
    with the flash message inside it, and the rating summary near the
    price out of band; any other request is redirected to the product page.

    Refused: the rules and status codes are the ones every request gets.
    Only the shape changes for HTMX — a 204 that sends the browser to the
    login page (a plain redirect would be followed and swapped in), or the
    403 with a page refresh.

    A GET, or a form with errors, renders ``inline_template_name`` — the
    piece that loads into the "Your review" area — for HTMX, and the
    standalone page (``template_name``) for everyone else.
    """

    inline_template_name = None

    def get_template_names(self):
        if is_htmx(self.request):
            return [self.inline_template_name]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            product=self.product, inline=is_htmx(self.request), **kwargs
        )

    def get_success_url(self):
        return f"{self.product.get_absolute_url()}#reviews"

    def handle_no_permission(self):
        if not is_htmx(self.request):
            return super().handle_no_permission()
        if not self.request.user.is_authenticated:
            login = redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Redirect"] = login.url
            return response
        return refreshing(HttpResponseForbidden())

    def finished(self):
        if not is_htmx(self.request):
            return redirect(self.get_success_url())
        context = {
            "product": self.product,
            "htmx": True,
            **reviews_section_context(self.request, self.product),
        }
        response = render(self.request, "reviews/partials/_reviews_swap.html", context)
        response["HX-Retarget"] = "#reviews"
        response["HX-Reswap"] = "outerHTML"
        return response


class ReviewFormMixin:
    """The write and edit form: the standalone page, or — for HTMX — the
    form alone, posting back inline. A form with errors comes back the same
    way, so with HTMX it replaces itself in place on the product page."""

    form_class = ReviewForm
    template_name = "reviews/review_form.html"
    inline_template_name = "reviews/partials/_review_form.html"


# One URL answers HTMX and plain requests differently, so caches must too.
vary_on_htmx = method_decorator(vary_on_headers("HX-Request"), name="dispatch")


@vary_on_htmx
class ReviewCreateView(
    ReviewFormMixin, ReviewActionMixin, UserPassesTestMixin, CreateView
):
    """Write a review. Anonymous → login; signed in but not allowed → 403.

    A customer who already has a review — a double click, a second tab —
    is sent back to the product with a message instead (or, inline, shown
    the section with it), and never gets a second row or an error page.
    """

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs["slug"])
        if Review.objects.own(request.user, self.product):
            return self.already_reviewed()
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return Review.objects.can_create(self.request.user, self.product)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.product = self.product
        # Two requests can both pass the check before either saves; the
        # unique constraint lets only one in. The savepoint keeps the
        # loser's failed insert from breaking the rest of the request.
        try:
            with transaction.atomic():
                super().form_valid(form)
        except IntegrityError:
            # Only the duplicate is expected — anything else re-raises.
            if not Review.objects.own(self.request.user, self.product):
                raise
            return self.already_reviewed()
        messages.success(self.request, "Thanks — your review is live.")
        return self.finished()

    def already_reviewed(self):
        messages.info(self.request, "You've already reviewed this product.")
        return self.finished()


class OwnReviewMixin(ReviewActionMixin, UserPassesTestMixin):
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
            if is_htmx(request):
                return refreshing(HttpResponseNotFound())
            raise Http404("You have no review of this product.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.review

    def test_func(self):
        return self.review is not None and self.allows(self.review)

    def allows(self, review):
        raise NotImplementedError


@vary_on_htmx
class ReviewUpdateView(ReviewFormMixin, OwnReviewMixin, UpdateView):
    """Edit your own review, while ``can_edit`` allows it."""

    def allows(self, review):
        return review.can_edit(self.request.user)

    def get_context_data(self, **kwargs):
        return super().get_context_data(editing=True, **kwargs)

    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, "Your review has been updated.")
        return self.finished()


@vary_on_htmx
class ReviewDeleteView(OwnReviewMixin, DeleteView):
    """Delete your own review: GET shows a confirmation — a page, or inline
    for HTMX — and changes nothing; only the POST deletes, through
    ``delete_by_author``."""

    template_name = "reviews/review_confirm_delete.html"
    inline_template_name = "reviews/partials/_review_delete_confirm.html"

    def allows(self, review):
        return review.can_delete(self.request.user)

    def form_valid(self, form):
        self.object.delete_by_author()
        messages.success(self.request, "Your review has been deleted.")
        return self.finished()


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


# --- The back office: restrictions --------------------------------------------
#
# Staff-only, like every back-office screen. Clearing is two steps: a GET
# confirmation that changes nothing, then a CSRF-protected POST.

ALREADY_CLEARED = "This restriction was already cleared; nothing was changed."


class ManageRestrictionListView(StaffRequiredMixin, ListView):
    """Every active restriction, newest first, 25 a page."""

    template_name = "reviews/manage_restrictions.html"
    context_object_name = "restrictions"
    paginate_by = 25
    extra_context = {"section": "reviews"}
    queryset = ReviewRestriction.objects.select_related("user", "product", "hidden_by")


class ClearRestrictionView(StaffRequiredMixin, View):
    """GET: a confirmation page naming the customer and product.
    POST: clear the restriction, so the customer may review again.

    A restriction that's already gone — cleared by someone else, or a
    second click — redirects to the list with an info message, by GET or
    POST, rather than a 404.
    """

    def get(self, request, pk):
        restriction = self.restriction(pk)
        if restriction is None:
            return self.already_cleared()
        return render(
            request,
            "reviews/manage_restriction_confirm_clear.html",
            {"restriction": restriction, "section": "reviews"},
        )

    def post(self, request, pk):
        restriction = self.restriction(pk)
        if restriction is None or not restriction.clear():
            return self.already_cleared()
        messages.success(
            request,
            f"Restriction cleared. {restriction.user.username} can review "
            f"{restriction.product.name} again.",
        )
        return redirect("reviews:manage_restrictions")

    def restriction(self, pk):
        return (
            ReviewRestriction.objects.select_related("user", "product")
            .filter(pk=pk)
            .first()
        )

    def already_cleared(self):
        messages.info(self.request, ALREADY_CLEARED)
        return redirect("reviews:manage_restrictions")
