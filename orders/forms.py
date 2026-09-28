"""The checkout form — the codebase's showcase of declarative validation.

Every rule is visible at its field declaration, in the style of data
annotations: field types validate (``EmailField``), field arguments
validate (``required``, ``max_length``, ``ChoiceField``), and the
``validators=[...]`` list carries the rest. No ``clean_*`` methods
and no ``clean()`` — none of its current rules need imperative validation.

The discount code rides in the same POST but is validated by its own
``CouponForm``: whether a code applies depends on the cart and the date,
which no declarative rule can see, and the showcase stays declarative.
"""

from django import forms
from django.core.validators import RegexValidator

from accounts.validators import US_STATES, zip_validator
from products.forms import StyledModelForm

from .models import Coupon, InvalidCouponError, Order
from .validators import validate_card_number, validate_expiry

cvv_validator = RegexValidator(r"^\d{3,4}$", "Enter the 3- or 4-digit CVV.")


class CheckoutForm(forms.Form):
    """One page, one POST: contact, shipping, billing, payment."""

    email = forms.EmailField(label="Email")

    shipping_name = forms.CharField(label="Full name", max_length=100)
    shipping_street = forms.CharField(label="Street address", max_length=200)
    shipping_line2 = forms.CharField(
        label="Apt, suite, etc. (optional)", max_length=200, required=False
    )
    shipping_city = forms.CharField(label="City", max_length=100)
    shipping_state = forms.ChoiceField(label="State", choices=US_STATES)
    shipping_zip = forms.CharField(
        label="ZIP code", max_length=10, validators=[zip_validator]
    )

    billing_name = forms.CharField(label="Full name", max_length=100)
    billing_street = forms.CharField(label="Street address", max_length=200)
    billing_line2 = forms.CharField(
        label="Apt, suite, etc. (optional)", max_length=200, required=False
    )
    billing_city = forms.CharField(label="City", max_length=100)
    billing_state = forms.ChoiceField(label="State", choices=US_STATES)
    billing_zip = forms.CharField(
        label="ZIP code", max_length=10, validators=[zip_validator]
    )

    save_shipping = forms.BooleanField(
        label="Save this address to my account", required=False
    )
    save_billing = forms.BooleanField(
        label="Save this address to my account", required=False
    )

    card_number = forms.CharField(
        label="Card number", max_length=23, validators=[validate_card_number]
    )
    card_expiry = forms.CharField(
        label="Expiry (MM/YY)", max_length=5, validators=[validate_expiry]
    )
    card_cvv = forms.CharField(label="CVV", max_length=4, validators=[cvv_validator])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "checkbox checkbox-sm"
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "select w-full"
            else:
                widget.attrs["class"] = "input w-full"

    # Field groups for the template — the form owns its own structure.

    def shipping_fields(self):
        return [self[name] for name in self.fields if name.startswith("shipping_")]

    def billing_fields(self):
        return [self[name] for name in self.fields if name.startswith("billing_")]

    def card_fields(self):
        return [self[name] for name in self.fields if name.startswith("card_")]


class CouponForm(forms.Form):
    """The checkout's discount code, redeemed against the customer's cart.

    Blank means no discount. A valid form leaves the redeemed ``Coupon``
    on ``self.coupon``; ``place_order`` redeems the code again as the
    backstop.

    ``applied_coupon_code`` carries the code the checkout last previewed,
    so a code typed over it but never applied can be caught before it
    changes the total the customer saw.
    """

    coupon_code = forms.CharField(
        label="Discount code",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "input w-full uppercase"}),
    )
    applied_coupon_code = forms.CharField(
        max_length=30, required=False, widget=forms.HiddenInput
    )

    def __init__(self, *args, cart, **kwargs):
        super().__init__(*args, **kwargs)
        self.cart = cart
        self.coupon = None

    def clean_coupon_code(self):
        code = self.cleaned_data["coupon_code"]
        if not code:
            return ""
        try:
            self.coupon = Coupon.objects.redeem(code, self.cart)
        except InvalidCouponError as error:
            raise forms.ValidationError(str(error)) from None
        return self.coupon.code

    def differs_from_preview(self):
        """Whether the submitted code isn't the one the checkout previewed."""
        submitted = Coupon.normalize_code(self.data.get("coupon_code", ""))
        applied = Coupon.normalize_code(self.data.get("applied_coupon_code", ""))
        return submitted != applied


class ManageCouponForm(StyledModelForm):
    """Back-office create and edit for discount codes.

    Once any order has used a code, its terms — code, percent, scope,
    products — lock, so a code means one deal for everyone who used it.
    Timing stays editable: Marketing can move the expiry or retire it.
    """

    LOCKED_AFTER_USE = ["code", "percent_off", "applies_to", "products"]

    class Meta:
        model = Coupon
        fields = [
            "code",
            "percent_off",
            "applies_to",
            "products",
            "expires_on",
            "is_active",
        ]
        labels = {
            "code": "Code",
            "percent_off": "Percent off",
            "applies_to": "Applies to",
            "expires_on": "Valid through",
            "is_active": "Active",
        }
        help_texts = {
            "code": "3–30 letters, digits, or hyphens. Saved in capitals.",
            "percent_off": "A whole number from 1 to 99.",
            "products": "Only for Selected products.",
            "expires_on": "The code works through the end of this day, store time.",
            "is_active": "Switch off to retire the code.",
        }
        widgets = {
            "expires_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.is_used:
            for name in self.LOCKED_AFTER_USE:
                self.fields[name].disabled = True

    def clean_code(self):
        return Coupon.normalize_code(self.cleaned_data["code"])

    def clean(self):
        cleaned_data = super().clean()
        applies_to = cleaned_data.get("applies_to")
        products = cleaned_data.get("products")
        if applies_to == Coupon.AppliesTo.PRODUCTS and not products:
            self.add_error(
                "products",
                "Pick at least one product, or change “Applies to” to Whole order.",
            )
        if applies_to == Coupon.AppliesTo.ORDER and products:
            self.add_error(
                "products", "Whole-order codes can't have products selected."
            )
        return cleaned_data


class OrderStatusForm(forms.ModelForm):
    """The back-office status dropdown — any of the four states, anytime.

    Guarding the workflow (no un-cancelling, no re-shipping a delivered
    order) is deliberately left as a student exercise.
    """

    class Meta:
        model = Order
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "select"})}
