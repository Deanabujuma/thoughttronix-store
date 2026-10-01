"""Project-wide pytest fixtures.

Shared test data lives here as plain fixtures — no factories. The suite
grows with the project. Every test writes uploaded media to its own
temporary MEDIA_ROOT, so nothing lands in the real ``media/``.
"""

import io
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from accounts.models import Address
from orders.models import Cart, CartItem, Coupon
from products.models import Category, Product, Tag


@pytest.fixture(autouse=True)
def temporary_media_root(settings, tmp_path):
    """Point MEDIA_ROOT at a per-test folder — seed tests included."""
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


@pytest.fixture
def customer(db):
    return get_user_model().objects.create_user(
        username="customer", password="customer123"
    )


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username="employee",
        password="employee123",
        is_staff=True,
        job_title="Junior Thought Curator",
    )


@pytest.fixture
def address(customer):
    """The customer's first saved address — so both of their defaults."""
    return Address.objects.create(
        user=customer,
        label="Home",
        name="Casey Monroe",
        street="214 Synapse Street",
        city="Canyon",
        state="TX",
        zip_code="79015",
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name="Home Assistants", slug="home-assistants")


@pytest.fixture
def product(category):
    return Product.objects.create(
        name="Seraphine Home Hub",
        slug="seraphine-home-hub",
        tagline="She's always listening. In a good way.",
        description="The flagship Seraphine hub with a seven-microphone array.",
        price=Decimal("349.99"),
        category=category,
    )


@pytest.fixture
def unavailable_product(category):
    return Product.objects.create(
        name="EchoPatch",
        slug="echopatch",
        tagline="Never miss a word. Anyone's.",
        price=Decimal("139.00"),
        is_available=False,
        category=category,
    )


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="bestseller", slug="bestseller")


@pytest.fixture
def cart(customer):
    return Cart.for_user(customer)


@pytest.fixture
def cart_item(cart, product):
    return CartItem.objects.create(cart=cart, product=product, quantity=2)


# Discount codes are dated relative to the store's own today, so the
# expiry rules hold whenever the suite runs — no clock freezing needed.


@pytest.fixture
def whole_order_coupon(db):
    return Coupon.objects.create(
        code="THOUGHTS10",
        percent_off=10,
        expires_on=timezone.localdate() + timedelta(days=30),
    )


@pytest.fixture
def product_coupon(product):
    coupon = Coupon.objects.create(
        code="HUB15",
        percent_off=15,
        applies_to=Coupon.AppliesTo.PRODUCTS,
        expires_on=timezone.localdate() + timedelta(days=30),
    )
    coupon.products.add(product)
    return coupon


@pytest.fixture
def expired_coupon(db):
    return Coupon.objects.create(
        code="SUMMER20",
        percent_off=20,
        expires_on=timezone.localdate() - timedelta(days=1),
    )


@pytest.fixture
def retired_coupon(db):
    return Coupon.objects.create(
        code="LAUNCH25",
        percent_off=25,
        expires_on=timezone.localdate() + timedelta(days=30),
        is_active=False,
    )


# Product images are generated in memory with Pillow: each fixture is one
# upload, sized to sit exactly on (or just past) a validation limit.


def _upload(width, height, image_format="PNG", mode="RGB", color="#3b82f6", **save):
    buffer = io.BytesIO()
    Image.new(mode, (width, height), color).save(buffer, image_format, **save)
    extension = {"JPEG": "jpg"}.get(image_format, image_format.lower())
    return SimpleUploadedFile(
        f"upload.{extension}",
        buffer.getvalue(),
        content_type=f"image/{extension}",
    )


@pytest.fixture
def png_upload():
    """A valid 800×1000 PNG — the smallest shortest side allowed."""
    return _upload(800, 1000)


@pytest.fixture
def jpeg_upload():
    return _upload(1200, 1500, "JPEG")


@pytest.fixture
def webp_upload():
    return _upload(1000, 1250, "WEBP")


@pytest.fixture
def transparent_png_upload():
    """A half-transparent PNG — its copies must keep the alpha channel."""
    return _upload(900, 900, mode="RGBA", color=(59, 130, 246, 128))


@pytest.fixture
def rotated_jpeg_upload():
    """A 1000×800 JPEG whose EXIF says "rotate 90°" — it displays 800×1000."""
    exif = Image.Exif()
    exif[0x0112] = 6  # Orientation: rotate 90° clockwise to display
    return _upload(1000, 800, "JPEG", exif=exif)


@pytest.fixture
def too_small_upload():
    """799 px on the shortest side — one pixel under the minimum."""
    return _upload(799, 1000)


@pytest.fixture
def widest_upload():
    """6000 px on the longest side — exactly the maximum."""
    return _upload(6000, 800)


@pytest.fixture
def too_wide_upload():
    """6001 px on the longest side — one pixel over the maximum."""
    return _upload(6001, 800)


@pytest.fixture
def gif_upload():
    """A real image in a format the store doesn't accept."""
    return _upload(800, 1000, "GIF", mode="P")


@pytest.fixture
def text_as_png_upload():
    """A text file wearing a .png name."""
    return SimpleUploadedFile("photo.png", b"not an image", content_type="image/png")


@pytest.fixture
def truncated_png_upload():
    """A PNG cut off halfway: the header parses, the pixels don't."""
    whole = _upload(800, 1000, compress_level=0).read()
    return SimpleUploadedFile("broken.png", whole[: len(whole) // 2])


@pytest.fixture
def oversized_upload():
    """A valid PNG padded to 5 MB + 1 byte."""
    image = _upload(800, 1000).read()
    padding = b"\0" * (5 * 1024 * 1024 + 1 - len(image))
    return SimpleUploadedFile("huge.png", image + padding, content_type="image/png")
