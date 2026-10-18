from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.mixins import StaffRequiredMixin
from reviews.models import Review
from wishlist.models import Wishlist

from .forms import CategoryForm, ProductForm, TagForm
from .models import Category, Product, Tag

REVIEWS_PER_PAGE = 10


class CatalogView(ListView):
    """The public product catalog: search, tag and category filters, pagination.

    Filters arrive as querystring parameters (``q``, ``tag``, ``category``)
    and compose freely.
    """

    template_name = "products/catalog.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        products = (
            Product.objects.select_related("category")
            .prefetch_related("tags")
            .with_ratings()
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            products = products.search(query)
        tag_slug = self.request.GET.get("tag", "")
        if tag_slug:
            products = products.filter(tags__slug=tag_slug)
        category_slug = self.request.GET.get("category", "")
        if category_slug:
            products = products.filter(category__slug=category_slug)
        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["active_tag"] = self.request.GET.get("tag", "")
        context["categories"] = Category.objects.all()
        context["tags"] = Tag.objects.all()
        return context


class CategoryView(CatalogView):
    """Browse a single category — the catalog scoped to one shelf."""

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
        return super().get_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class ProductDetailView(DetailView):
    """A single product at its slug URL, with its wishlist button's state,
    its rating summary, and its reviews.

    The visitor's own review is pinned on its own, so it's left out of
    the public list below it.
    """

    template_name = "products/detail.html"
    context_object_name = "product"
    queryset = Product.objects.select_related("category").prefetch_related("tags")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user, product = self.request.user, self.object
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
            self.request.GET.get("reviews", 1)
        )
        context.update(
            saved=Wishlist.has_saved(user, product),
            rating=Review.objects.summary_for(product),
            own_review=own_review,
            # The author may always delete; Edit shows only while allowed.
            can_edit_review=bool(own_review and own_review.can_edit(user)),
            review_state=Review.objects.visitor_state(user, product, own_review),
            reviews=review_page,
        )
        return context


# --- The back office --------------------------------------------------------
#
# Staff-only catalog management. Every view gates on StaffRequiredMixin;
# URLs use pks per the URL conventions. The ``section`` context entry
# drives the active tab in the staff shell (backoffice/base.html).


class ManageProductListView(StaffRequiredMixin, ListView):
    """The back-office product list — every product, available or not."""

    template_name = "products/manage_products.html"
    context_object_name = "products"
    extra_context = {"section": "products"}

    def get_queryset(self):
        return Product.objects.select_related("category")


class ManageProductCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/manage_product_form.html"
    success_url = reverse_lazy("products:manage_products")
    success_message = "“%(name)s” created."
    extra_context = {"section": "products"}


class ManageProductUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/manage_product_form.html"
    success_url = reverse_lazy("products:manage_products")
    success_message = "“%(name)s” saved."
    extra_context = {"section": "products"}


class ManageProductDeleteView(StaffRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Product
    context_object_name = "product"
    template_name = "products/manage_product_confirm_delete.html"
    success_url = reverse_lazy("products:manage_products")
    success_message = "Product deleted."
    extra_context = {"section": "products"}


class ManageCatalogView(StaffRequiredMixin, TemplateView):
    """Categories and tags on one management page."""

    template_name = "products/manage_catalog.html"
    extra_context = {"section": "catalog"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.annotate(
            product_count=Count("products")
        )
        context["tags"] = Tag.objects.annotate(product_count=Count("products"))
        return context


class ManageCategoryCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "products/manage_catalog_form.html"
    success_url = reverse_lazy("products:manage_catalog")
    success_message = "“%(name)s” created."
    extra_context = {"section": "catalog", "kind": "category"}


class ManageCategoryUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "products/manage_catalog_form.html"
    success_url = reverse_lazy("products:manage_catalog")
    success_message = "“%(name)s” saved."
    extra_context = {"section": "catalog", "kind": "category"}


class ManageTagCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Tag
    form_class = TagForm
    template_name = "products/manage_catalog_form.html"
    success_url = reverse_lazy("products:manage_catalog")
    success_message = "“%(name)s” created."
    extra_context = {"section": "catalog", "kind": "tag"}


class ManageTagUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Tag
    form_class = TagForm
    template_name = "products/manage_catalog_form.html"
    success_url = reverse_lazy("products:manage_catalog")
    success_message = "“%(name)s” saved."
    extra_context = {"section": "catalog", "kind": "tag"}
