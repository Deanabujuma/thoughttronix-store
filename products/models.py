from dataclasses import dataclass

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.templatetags.static import static
from django.urls import reverse
from django.utils.functional import cached_property

from . import images

# Categories with a dedicated placeholder illustration; anything else
# falls back to default.svg. A product without a usable uploaded image
# shows its category's placeholder.
PLACEHOLDER_CATEGORIES = {
    "home-assistants",
    "neural-implants",
    "neural-wearables",
    "accessories",
    "defense",
    "legacy-products",
}


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:category", kwargs={"slug": self.slug})

    @property
    def placeholder_image(self):
        """Static path of the placeholder image shown for this category's products."""
        if self.slug in PLACEHOLDER_CATEGORIES:
            return f"images/placeholders/{self.slug}.svg"
        return "images/placeholders/default.svg"

    @property
    def placeholder_alt(self):
        """Alt text for the placeholder — honest that it isn't a product photo."""
        return f"{self.name} category placeholder (no product photo yet)"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class DisplayImage:
    """What a template needs to draw one product image."""

    url: str
    alt: str
    width: int | None = None
    height: int | None = None
    is_placeholder: bool = False


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.filter(is_available=True)

    def search(self, text):
        """Simple icontains search over name and description."""
        return self.filter(
            models.Q(name__icontains=text) | models.Q(description__icontains=text)
        )


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")
    # The uploaded original; its WebP display copies sit beside it. Files
    # are written by products/images.py, never by the field itself.
    image = models.ImageField(max_length=200, blank=True)
    image_alt = models.CharField(
        "image description",
        max_length=250,
        blank=True,
        help_text=(
            "Describe what the image shows for people using screen readers, "
            "including any important words printed in it. Leave blank to use "
            "“Product image of <name>”."
        ),
    )
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save, then drop the replaced or cleared image's files after commit."""
        super().save(*args, **kwargs)
        saved = getattr(self, "_saved_image_name", "")
        if saved and saved != self.image.name:
            images.delete_after_commit(saved)
        self._saved_image_name = self.image.name

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"slug": self.slug})

    @classmethod
    def from_db(cls, db, field_names, values):
        # Remember the stored image, so save() can spot a replacement.
        product = super().from_db(db, field_names, values)
        if "image" not in product.get_deferred_fields():
            product._saved_image_name = product.image.name
        return product

    def set_image(self, processed):
        """Store a processed image's files and point at them; ``None`` clears.

        The old files stay until ``save()`` commits.
        """
        if processed is None:
            self.image = ""
            self.image_width = self.image_height = None
        else:
            self.image = images.save_image(processed)
            self.image_width = processed.detail_width
            self.image_height = processed.detail_height

    @cached_property
    def card_image(self):
        """The catalog-card image, or the category placeholder."""
        return self._display_image(images.card_name)

    @cached_property
    def detail_image(self):
        """The detail-page image with its dimensions, or the placeholder."""
        return self._display_image(
            images.detail_name, self.image_width, self.image_height
        )

    def _display_image(self, copy_name, width=None, height=None):
        # A missing copy falls back to the placeholder, never a broken image.
        if self.image:
            name = copy_name(self.image.name)
            storage = self.image.storage
            if storage.exists(name):
                return DisplayImage(
                    url=storage.url(name),
                    alt=self.image_alt or f"Product image of {self.name}",
                    width=width,
                    height=height,
                )
        return DisplayImage(
            url=static(self.category.placeholder_image),
            alt=self.category.placeholder_alt,
            is_placeholder=True,
        )


@receiver(post_delete, sender=Product)
def delete_product_image_files(sender, instance, **kwargs):
    """Remove a deleted product's image files once the delete commits.

    A receiver rather than ``Product.delete()`` so bulk deletes — the seed
    command's wipe — clean up too.
    """
    images.delete_after_commit(instance.image.name)
