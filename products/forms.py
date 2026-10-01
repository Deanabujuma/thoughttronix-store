"""Back-office forms for the catalog models.

ModelForms inherit the models' own rules (name required, slug unique);
the explicit ``price`` declaration adds the one rule the model doesn't
carry — the price must be positive. Widgets get their DaisyUI classes
in one shared ``__init__`` loop, as on ``CheckoutForm``.

The product image is not a model-form field: ``clean_image`` hands the
upload to ``products/images.py``, which validates it and builds the display
copies before anything is saved.
"""

from decimal import Decimal

from django import forms
from django.db import transaction

from . import images
from .models import Category, Product, Tag

CONFLICT_MESSAGE = (
    "Choose a new image or tick Remove image, not both. "
    "If uploading, please select the file again."
)


class StyledModelForm(forms.ModelForm):
    """Base form that dresses every widget in DaisyUI classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.FileInput):
                widget.attrs["class"] = "file-input w-full"
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "toggle toggle-primary"
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = "textarea w-full"
                widget.attrs.setdefault("rows", 6)
            elif isinstance(widget, forms.SelectMultiple):
                widget.attrs["class"] = "select h-auto w-full"
                widget.attrs.setdefault("size", 8)
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "select w-full"
            else:
                widget.attrs["class"] = "input w-full"


class ProductForm(StyledModelForm):
    price = forms.DecimalField(
        label="Price (USD)",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    # Declared before ``image`` so it is cleaned first: ``clean_image``
    # rejects a new file sent together with Remove image.
    remove_image = forms.BooleanField(label="Remove image", required=False)
    image = forms.FileField(
        label="Product image",
        required=False,
        help_text=images.UPLOAD_RULES,
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(f"image/{ext}" for ext in ("jpeg", "png", "webp"))
            }
        ),
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "tagline",
            "description",
            "price",
            "category",
            "tags",
            "is_available",
            "image_alt",
        ]

    field_order = [*Meta.fields[:-1], "remove_image", "image", "image_alt"]

    # Shown when another field fails: browsers never re-send a chosen file.
    reselect_note = (
        "This file wasn't saved because another field needs attention. "
        + images.RESELECT_NOTE
    )

    def clean_image(self):
        upload = self.cleaned_data.get("image")
        if upload:
            if self.cleaned_data.get("remove_image"):
                raise forms.ValidationError(CONFLICT_MESSAGE, code="conflict")
            self.processed_image = images.process_upload(upload)
        return upload

    def save(self, commit=True):
        product = super().save(commit=False)
        processed = getattr(self, "processed_image", None)
        if processed or self.cleaned_data.get("remove_image"):
            product.set_image(processed)
        if commit:
            try:
                with transaction.atomic():
                    product.save()
                    self._save_m2m()
            except Exception:
                if processed:  # the new files belong to a save that failed
                    images.delete_image_files(product.image.name)
                raise
        return product


class CategoryForm(StyledModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug"]


class TagForm(StyledModelForm):
    class Meta:
        model = Tag
        fields = ["name", "slug"]
