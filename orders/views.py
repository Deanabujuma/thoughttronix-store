"""Cart and checkout views — thin per the architecture convention.

The three HTMX interactions of the core live here: add-to-cart, quantity
change, and line removal. Each renders a partial (never ``base.html``);
the responses carry the navbar badge as an out-of-band swap via the
``oob_badge`` context flag. Checkout is conventional full-page work:
validate the form, hand everything to ``place_order``.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.mixins import StaffRequiredMixin
from accounts.models import Address
from products.models import Product

from .forms import CheckoutForm, CouponForm, ManageCouponForm, OrderStatusForm
from .models import Cart, CartItem, Coupon, InvalidCouponError, Order
from .services import place_order


class CartView(LoginRequiredMixin, TemplateView):
    """The customer's cart page."""

    template_name = "orders/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cart"] = Cart.for_user(self.request.user)
        return context


class AddToCartView(LoginRequiredMixin, View):
    """HTMX: add a product; the button swaps and the badge updates OOB.

    Looks the product up through ``available()``, so adding an
    unavailable product 404s — the same not-for-sale semantics as the
    public catalog.
    """

    def post(self, request, pk):
        product = get_object_or_404(Product.objects.available(), pk=pk)
        item = Cart.for_user(request.user).add(product)
        return render(
            request,
            "orders/partials/_add_button.html",
            {"product": product, "in_cart": item.quantity, "oob_badge": True},
        )


class CartItemActionView(LoginRequiredMixin, View):
    """Base for HTMX line mutations: act, then re-render the cart contents.

    Items are always fetched through the owner's cart — never by bare pk.
    """

    def post(self, request, pk):
        item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        self.act(item)
        return render(
            request,
            "orders/partials/_cart_contents.html",
            {"cart": item.cart, "oob_badge": True},
        )

    def act(self, item):
        raise NotImplementedError


class IncrementCartItemView(CartItemActionView):
    def act(self, item):
        item.increment()


class DecrementCartItemView(CartItemActionView):
    def act(self, item):
        item.decrement()


class RemoveCartItemView(CartItemActionView):
    def act(self, item):
        item.delete()


ADDRESS_KINDS = ("shipping", "billing")


class CheckoutView(LoginRequiredMixin, FormView):
    """The single checkout page: validate the form, hand off to the service.

    A cart that can't check out (empty, or holding a product that has
    since become unavailable) is sent back to the cart page to be fixed —
    ``place_order`` enforces the same rules transactionally as the
    backstop, and a backstop failure sends the customer to the cart too.

    The discount code posts with the checkout but validates in its own
    ``CouponForm``; both forms must pass before an order is placed.
    """

    template_name = "orders/checkout.html"
    form_class = CheckoutForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        cart = Cart.for_user(request.user)
        if not cart.items.exists():
            messages.info(request, "Your cart is empty — add something first.")
            return redirect("orders:cart")
        unavailable = [
            line.product.name for line in cart.lines() if not line.product.is_available
        ]
        if unavailable:
            messages.warning(
                request,
                f"No longer available: {', '.join(unavailable)}. "
                "Remove them from the cart to check out.",
            )
            return redirect("orders:cart")
        return super().dispatch(request, *args, **kwargs)

    def get_coupon_form(self):
        data = self.request.POST if self.request.method == "POST" else None
        return CouponForm(data, cart=Cart.for_user(self.request.user))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        coupon_form = self.get_coupon_form()
        # Validate both, so every error shows at once.
        if all([form.is_valid(), coupon_form.is_valid()]):
            return self.form_valid(form, coupon_form)
        return self.form_invalid(form, coupon_form)

    def form_invalid(self, form, coupon_form):
        return self.render_to_response(
            self.get_context_data(form=form, coupon_form=coupon_form)
        )

    def get_initial(self):
        """Open with each address section filled from its default."""
        initial = super().get_initial()
        addresses = self.request.user.addresses
        for prefix in ADDRESS_KINDS:
            default = addresses.filter(**{f"is_default_{prefix}": True}).first()
            if default:
                initial.update(default.as_checkout_initial(prefix))
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        coupon_form = context.setdefault("coupon_form", self.get_coupon_form())
        context["pricing"] = Cart.for_user(self.request.user).priced(coupon_form.coupon)
        saved = list(self.request.user.addresses.all())
        context["saved_addresses"] = saved
        for prefix in ADDRESS_KINDS:
            context[f"default_{prefix}_pk"] = next(
                (a.pk for a in saved if getattr(a, f"is_default_{prefix}")), None
            )
        return context

    def form_valid(self, form, coupon_form):
        cart = Cart.for_user(self.request.user)
        try:
            order = place_order(
                cart,
                self.request.user,
                form.cleaned_data,
                coupon_code=coupon_form.cleaned_data["coupon_code"] or None,
            )
        except InvalidCouponError as error:
            # The code passed its form but not the backstop — it expired
            # or was retired in between. Show it beside the field.
            coupon_form.add_error("coupon_code", str(error))
            coupon_form.coupon = None
            return self.form_invalid(form, coupon_form)
        except ValueError as error:
            # The cart changed between page load and submit.
            messages.warning(self.request, str(error))
            return redirect("orders:cart")
        # Saving is a convenience on top of the order, never part of it:
        # the order already holds its own copy of both addresses.
        for prefix in ADDRESS_KINDS:
            if form.cleaned_data[f"save_{prefix}"]:
                Address.objects.save_from_checkout(
                    self.request.user, form.cleaned_data, prefix
                )
        messages.success(self.request, f"Order {order.number} placed. Thank you!")
        return redirect(reverse("orders:confirmation", kwargs={"pk": order.pk}))


class CheckoutAddressView(LoginRequiredMixin, View):
    """HTMX: one checkout address section, filled from a saved address.

    The fields come back as ordinary, editable form fields, so checkout
    still posts and validates exactly as if they had been typed.
    """

    def get(self, request, kind):
        address_pk = request.GET.get("address", "")
        if kind not in ADDRESS_KINDS or not address_pk.isdigit():
            raise Http404
        address = get_object_or_404(Address, pk=address_pk, user=request.user)
        form = CheckoutForm(initial=address.as_checkout_initial(kind))
        return render(
            request,
            "orders/partials/_address_fields.html",
            {"fields": getattr(form, f"{kind}_fields")()},
        )


class CheckoutCouponView(LoginRequiredMixin, View):
    """HTMX: apply or remove the discount code, previewing the order.

    Nothing is saved — the code lives only in the checkout form, and
    ``place_order`` redeems it again on submit. Returns the code control
    plus the order summary and place-order button out-of-band. A failed
    Apply leaves no code applied; a blank code is a Remove.
    """

    http_method_names = ["post"]

    def post(self, request):
        cart = Cart.for_user(request.user)
        coupon_form = CouponForm(request.POST, cart=cart)
        coupon_form.is_valid()
        return render(
            request,
            "orders/partials/_coupon_field.html",
            {
                "coupon_form": coupon_form,
                "pricing": cart.priced(coupon_form.coupon),
                "oob": True,
            },
        )


class OwnOrdersMixin(LoginRequiredMixin):
    """Orders are always fetched through the owner — never by bare pk."""

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderConfirmationView(OwnOrdersMixin, DetailView):
    template_name = "orders/confirmation.html"
    context_object_name = "order"


class OrderHistoryView(OwnOrdersMixin, ListView):
    """The customer's orders, most recent first per the model ordering."""

    template_name = "orders/order_history.html"
    context_object_name = "orders"


class OrderDetailView(OwnOrdersMixin, DetailView):
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("items")


# --- The back office --------------------------------------------------------
#
# Staff-only order oversight: every customer's orders, filterable by
# status, with the status dropdown on the detail page. The ``section``
# context entry drives the active tab in the staff shell.


class ManageOrderListView(StaffRequiredMixin, ListView):
    """All orders, most recent first, filterable via ``?status=``."""

    template_name = "orders/manage_orders.html"
    context_object_name = "orders"
    paginate_by = 20
    extra_context = {"section": "orders"}

    def get_queryset(self):
        orders = Order.objects.select_related("user")
        status = self.request.GET.get("status", "")
        if status in Order.Status.values:
            orders = orders.filter(status=status)
        return orders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Order.Status.choices
        context["active_status"] = self.request.GET.get("status", "")
        return context


class ManageOrderDetailView(StaffRequiredMixin, DetailView):
    """Any order's detail, with the status form alongside."""

    template_name = "orders/manage_order_detail.html"
    context_object_name = "order"
    queryset = Order.objects.select_related("user").prefetch_related("items")
    extra_context = {"section": "orders"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_form"] = OrderStatusForm(instance=self.object)
        return context


class UpdateOrderStatusView(StaffRequiredMixin, View):
    """POST-only: set an order's status from the back-office dropdown."""

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"{order.number} is now {order.get_status_display().lower()}.",
            )
        else:
            messages.error(request, "That isn't a status an order can have.")
        return redirect("orders:manage_order_detail", pk=order.pk)


# --- Discount codes (back office) ---------------------------------------------
#
# Marketing's screens: list with a status filter, create, edit (terms lock
# after first use), retire, and delete — for never-used codes only.


class ManageCouponListView(StaffRequiredMixin, ListView):
    """Every discount code, newest first, filterable via ``?status=``."""

    template_name = "orders/manage_coupons.html"
    context_object_name = "coupons"
    paginate_by = 20
    extra_context = {"section": "coupons"}

    def get_queryset(self):
        return (
            Coupon.objects.with_status(self.active_status())
            .with_use_count()
            .annotate(product_count=Count("products", distinct=True))
            # Aggregating queries skip Meta.ordering; restate newest-first.
            .order_by("-created_at", "-pk")
        )

    def active_status(self):
        status = self.request.GET.get("status", "")
        return status if status in Coupon.Status.values else ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Coupon.Status.choices
        context["active_status"] = self.active_status()
        return context


class ManageCouponCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Coupon
    form_class = ManageCouponForm
    template_name = "orders/manage_coupon_form.html"
    success_url = reverse_lazy("orders:manage_coupons")
    success_message = "“%(code)s” created."
    extra_context = {"section": "coupons"}


class ManageCouponUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Coupon
    form_class = ManageCouponForm
    template_name = "orders/manage_coupon_form.html"
    success_url = reverse_lazy("orders:manage_coupons")
    success_message = "“%(code)s” saved."
    extra_context = {"section": "coupons"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["use_count"] = self.object.orders.count()
        return context


class ManageCouponRetireView(StaffRequiredMixin, View):
    """POST-only: switch a code off. Past orders keep their snapshot."""

    def post(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk)
        coupon.is_active = False
        coupon.save(update_fields=["is_active"])
        messages.success(
            request, f"“{coupon.code}” retired. Past orders are unchanged."
        )
        return redirect("orders:manage_coupons")


class ManageCouponDeleteView(StaffRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete a code no order has used; a used code 404s — retire it instead."""

    queryset = Coupon.objects.filter(orders__isnull=True)
    context_object_name = "coupon"
    template_name = "orders/manage_coupon_confirm_delete.html"
    success_url = reverse_lazy("orders:manage_coupons")
    success_message = "Discount code deleted."
    extra_context = {"section": "coupons"}
