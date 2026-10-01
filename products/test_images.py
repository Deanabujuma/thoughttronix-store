"""Product images: upload, validation, display copies, display, and cleanup."""

import io
from http import HTTPStatus

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.db import IntegrityError, transaction
from django.urls import reverse
from PIL import Image

from . import images
from .forms import ProductForm
from .models import Product

pytestmark = pytest.mark.django_db


def product_data(category, **overrides):
    data = {
        "name": "MindSync Sleep Halo",
        "slug": "mindsync-sleep-halo",
        "price": "199.99",
        "is_available": "on",
        "category": str(category.pk),
    }
    data.update(overrides)
    return data


def edit_data(product, **overrides):
    return product_data(
        product.category, name=product.name, slug=product.slug, **overrides
    )


def upload_to(client, product, upload, **overrides):
    """POST the edit form for ``product`` with ``upload`` as its new image."""
    url = reverse("products:manage_product_update", kwargs={"pk": product.pk})
    return client.post(url, edit_data(product, image=upload, **overrides))


def _png_bytes(width, height):
    buffer = io.BytesIO()
    Image.new("RGB", (width, height)).save(buffer, "PNG")
    return buffer.getvalue()


def open_stored(name):
    with default_storage.open(name) as stored:
        image = Image.open(stored)
        image.load()
        return image


@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client


@pytest.fixture
def product_with_image(staff_client, product, jpeg_upload):
    upload_to(staff_client, product, jpeg_upload)
    product.refresh_from_db()
    assert product.image
    return product


# --- Uploading a valid image ---------------------------------------------------


def test_creating_a_product_with_an_image(staff_client, category, png_upload):
    response = staff_client.post(
        reverse("products:manage_product_create"),
        product_data(category, image=png_upload),
    )

    assert response.status_code == HTTPStatus.FOUND
    product = Product.objects.get(slug="mindsync-sleep-halo")
    folder, filename = product.image.name.rsplit("/", 1)
    assert folder.startswith("products/") and len(folder) == len("products/") + 32
    assert filename == "original.png"
    for name in ("original.png", "card.webp", "detail.webp"):
        assert default_storage.exists(f"{folder}/{name}")


@pytest.mark.parametrize(
    ("upload_fixture", "extension"),
    [("png_upload", "png"), ("jpeg_upload", "jpg"), ("webp_upload", "webp")],
)
def test_each_accepted_format_is_stored_under_its_detected_extension(
    request, staff_client, product, upload_fixture, extension
):
    upload = request.getfixturevalue(upload_fixture)
    upload.name = "mislabelled.gif"  # the name is ignored; the content decides

    upload_to(staff_client, product, upload)

    product.refresh_from_db()
    assert product.image.name.endswith(f"/original.{extension}")


def test_display_copies_fit_their_boxes_without_cropping(product_with_image):
    # The fixture uploads a 1200×1500 JPEG.
    card = open_stored(images.card_name(product_with_image.image.name))
    detail = open_stored(images.detail_name(product_with_image.image.name))

    assert (card.format, card.size) == ("WEBP", (640, 800))
    assert (detail.format, detail.size) == ("WEBP", (1200, 1500))
    assert (product_with_image.image_width, product_with_image.image_height) == (
        1200,
        1500,
    )


def test_small_images_are_never_enlarged(staff_client, product, png_upload):
    upload_to(staff_client, product, png_upload)  # 800×1000

    product.refresh_from_db()
    detail = open_stored(images.detail_name(product.image.name))
    assert detail.size == (800, 1000)


def test_copies_are_turned_upright_and_carry_no_metadata(
    staff_client, product, rotated_jpeg_upload
):
    upload_to(staff_client, product, rotated_jpeg_upload)

    product.refresh_from_db()
    card = open_stored(images.card_name(product.image.name))
    assert card.size == (640, 800)  # 1000×800 stored, displayed portrait
    assert not card.getexif()


def test_transparency_survives_in_the_copies(
    staff_client, product, transparent_png_upload
):
    upload_to(staff_client, product, transparent_png_upload)

    product.refresh_from_db()
    assert open_stored(images.card_name(product.image.name)).mode == "RGBA"


# --- Display -------------------------------------------------------------------


def test_catalog_shows_the_lazy_card_copy(client, product_with_image):
    html = client.get(reverse("products:catalog")).content.decode()

    card_url = default_storage.url(images.card_name(product_with_image.image.name))
    assert f'src="{card_url}"' in html
    assert 'alt="Product image of Seraphine Home Hub"' in html
    assert 'loading="lazy"' in html
    assert "relative aspect-[4/5]" in html
    assert "absolute inset-0 h-full w-full object-contain" in html


def test_detail_shows_the_eager_detail_copy_with_dimensions(client, product_with_image):
    html = client.get(product_with_image.get_absolute_url()).content.decode()

    detail_url = default_storage.url(images.detail_name(product_with_image.image.name))
    assert f'src="{detail_url}"' in html
    assert 'width="1200" height="1500"' in html
    assert 'loading="lazy"' not in html


def test_image_alt_replaces_the_generated_alt_text(client, product_with_image):
    product_with_image.image_alt = "A glowing hub on a nightstand."
    product_with_image.save()

    html = client.get(product_with_image.get_absolute_url()).content.decode()

    assert 'alt="A glowing hub on a nightstand."' in html


def test_products_without_an_image_show_the_category_placeholder(client, product):
    catalog = client.get(reverse("products:catalog")).content.decode()
    detail = client.get(product.get_absolute_url()).content.decode()

    placeholder_alt = (
        'alt="Home Assistants category placeholder (no product photo yet)"'
    )
    for html in (catalog, detail):
        assert "images/placeholders/home-assistants.svg" in html
        assert placeholder_alt in html


def test_placeholder_ignores_image_alt(client, product):
    product.image_alt = "Describes a photo that isn't there."
    product.save()

    html = client.get(product.get_absolute_url()).content.decode()

    assert "Describes a photo" not in html
    assert "category placeholder (no product photo yet)" in html


@pytest.mark.parametrize(
    ("missing", "page"),
    [(images.card_name, "catalog"), (images.detail_name, "detail")],
)
def test_a_missing_copy_falls_back_to_the_placeholder(
    client, product_with_image, missing, page
):
    default_storage.delete(missing(product_with_image.image.name))
    url = (
        reverse("products:catalog")
        if page == "catalog"
        else product_with_image.get_absolute_url()
    )

    html = client.get(url).content.decode()

    assert "images/placeholders/home-assistants.svg" in html
    assert "category placeholder (no product photo yet)" in html
    assert "Product image of" not in html
    assert 'width="1200"' not in html


def test_a_missing_folder_falls_back_on_both_pages(client, product_with_image):
    images.delete_image_files(product_with_image.image.name)

    for url in (reverse("products:catalog"), product_with_image.get_absolute_url()):
        html = client.get(url).content.decode()
        assert "images/placeholders/home-assistants.svg" in html, url


# --- Validation ----------------------------------------------------------------


def rejection(upload):
    with pytest.raises(ValidationError) as caught:
        images.process_upload(upload)
    (message,) = caught.value.messages
    assert message.endswith(images.RESELECT_NOTE)
    return message


@pytest.mark.parametrize("upload_fixture", ["gif_upload", "text_as_png_upload"])
def test_unsupported_formats_are_rejected(request, upload_fixture):
    message = rejection(request.getfixturevalue(upload_fixture))

    assert message.startswith("Upload a JPEG, PNG, or WebP image.")


def test_a_damaged_image_is_rejected(truncated_png_upload):
    message = rejection(truncated_png_upload)

    assert "may be damaged" in message
    assert "Upload a JPEG, PNG, or WebP image." in message


def test_files_over_5_mb_are_rejected_with_their_size(oversized_upload):
    message = rejection(oversized_upload)

    assert message.startswith("This file is 5.1 MB. The maximum is 5 MB.")


def test_5_mb_exactly_is_accepted():
    image = _png_bytes(800, 1000)
    upload = SimpleUploadedFile(
        "limit.png", image + b"\0" * (images.MAX_UPLOAD_BYTES - len(image))
    )

    assert images.process_upload(upload).extension == "png"


def test_799_px_is_rejected_and_800_px_accepted(too_small_upload, png_upload):
    message = rejection(too_small_upload)

    assert message.startswith(
        "This image is 799×1000 px. It must be at least 800 px on its shortest side."
    )
    assert images.process_upload(png_upload)


def test_6001_px_is_rejected_and_6000_px_accepted(too_wide_upload, widest_upload):
    message = rejection(too_wide_upload)

    assert message.startswith(
        "This image is 6001×800 px. It must be at most 6000 px on its longest side."
    )
    assert images.process_upload(widest_upload)


def test_a_rejected_upload_keeps_the_existing_image(
    staff_client, product_with_image, too_small_upload
):
    before = product_with_image.image.name

    response = upload_to(staff_client, product_with_image, too_small_upload)

    assert response.status_code == HTTPStatus.OK
    html = response.content.decode()
    assert "It must be at least 800 px on its shortest side." in html
    assert "Please select the file again. Any existing image is unchanged." in html
    product_with_image.refresh_from_db()
    assert product_with_image.image.name == before
    assert default_storage.exists(images.card_name(before))


def test_a_rejected_upload_writes_nothing(staff_client, category, gif_upload):
    staff_client.post(
        reverse("products:manage_product_create"),
        product_data(category, image=gif_upload),
    )

    assert not Product.objects.exists()
    assert not default_storage.exists("products")


def test_remove_image_with_a_new_file_is_rejected(
    staff_client, product_with_image, png_upload
):
    before = product_with_image.image.name

    response = upload_to(
        staff_client, product_with_image, png_upload, remove_image="on"
    )

    assert response.status_code == HTTPStatus.OK
    assert (
        "Choose a new image or tick Remove image, not both. "
        "If uploading, please select the file again."
    ) in response.content.decode()
    product_with_image.refresh_from_db()
    assert product_with_image.image.name == before


# --- File lifecycle ------------------------------------------------------------


def folder_files_exist(original_name):
    """Existence of [original, card, detail, their folder]."""
    return [
        default_storage.exists(name)
        for name in (
            original_name,
            images.card_name(original_name),
            images.detail_name(original_name),
            original_name.rsplit("/", 1)[0],
        )
    ]


def test_replacing_deletes_the_old_files_after_commit(
    staff_client, product_with_image, png_upload, django_capture_on_commit_callbacks
):
    old = product_with_image.image.name

    with django_capture_on_commit_callbacks(execute=True):
        upload_to(staff_client, product_with_image, png_upload)

    product_with_image.refresh_from_db()
    assert product_with_image.image.name != old
    assert folder_files_exist(old) == [False, False, False, False]
    assert folder_files_exist(product_with_image.image.name) == [True, True, True, True]


def test_removing_clears_the_image_and_its_files(
    staff_client, product_with_image, django_capture_on_commit_callbacks
):
    old = product_with_image.image.name
    url = reverse(
        "products:manage_product_update", kwargs={"pk": product_with_image.pk}
    )

    with django_capture_on_commit_callbacks(execute=True):
        staff_client.post(url, edit_data(product_with_image, remove_image="on"))

    product_with_image.refresh_from_db()
    assert not product_with_image.image
    assert product_with_image.image_width is None
    assert folder_files_exist(old) == [False, False, False, False]
    assert product_with_image.card_image.is_placeholder


def test_deleting_a_product_deletes_its_files(
    staff_client, product_with_image, django_capture_on_commit_callbacks
):
    old = product_with_image.image.name
    url = reverse(
        "products:manage_product_delete", kwargs={"pk": product_with_image.pk}
    )

    with django_capture_on_commit_callbacks(execute=True):
        staff_client.post(url)

    assert folder_files_exist(old) == [False, False, False, False]


def test_bulk_deletes_clean_up_too(
    product_with_image, django_capture_on_commit_callbacks
):
    old = product_with_image.image.name

    with django_capture_on_commit_callbacks(execute=True):
        Product.objects.all().delete()

    assert folder_files_exist(old) == [False, False, False, False]


def test_the_seed_wipe_cleans_up_uploaded_images(
    product_with_image, django_capture_on_commit_callbacks
):
    old = product_with_image.image.name

    with django_capture_on_commit_callbacks(execute=True):
        call_command("seed", stdout=io.StringIO())

    assert folder_files_exist(old) == [False, False, False, False]


def test_a_rolled_back_change_deletes_nothing(
    product_with_image, django_capture_on_commit_callbacks
):
    old = product_with_image.image.name

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        with pytest.raises(RuntimeError), transaction.atomic():
            product_with_image.image = ""
            product_with_image.save()
            raise RuntimeError("the save failed after all")

    assert callbacks == []
    assert folder_files_exist(old) == [True, True, True, True]


def test_a_failed_save_keeps_the_old_image_and_drops_the_new_files(
    product_with_image, png_upload, monkeypatch, django_capture_on_commit_callbacks
):
    old = product_with_image.image.name
    form = ProductForm(
        edit_data(product_with_image),
        {"image": png_upload},
        instance=Product.objects.get(pk=product_with_image.pk),
    )
    assert form.is_valid(), form.errors

    def failing_save(self, *args, **kwargs):
        raise IntegrityError("the database said no")

    monkeypatch.setattr(Product, "save", failing_save)
    with (
        django_capture_on_commit_callbacks(execute=True),
        pytest.raises(IntegrityError),
    ):
        form.save()

    assert folder_files_exist(old) == [True, True, True, True]
    assert default_storage.listdir("products")[0] == [old.split("/")[1]]


# --- The back-office upload experience -----------------------------------------


def edit_page(client, product):
    url = reverse("products:manage_product_update", kwargs={"pk": product.pk})
    return client.get(url).content.decode()


def test_the_form_accepts_files_and_states_the_rules(staff_client, product):
    html = edit_page(staff_client, product)

    assert 'enctype="multipart/form-data"' in html
    assert 'accept="image/jpeg,image/png,image/webp"' in html
    assert 'class="file-input w-full"' in html
    assert "JPEG, PNG, or WebP · up to 5 MB · 800–6000 px" in html
    assert "including any important words printed in it" in html


def test_the_edit_form_previews_the_current_image(staff_client, product_with_image):
    html = edit_page(staff_client, product_with_image)

    card_url = default_storage.url(images.card_name(product_with_image.image.name))
    assert f'src="{card_url}"' in html
    assert "Current image" in html
    assert "Remove image" in html


def test_without_an_image_the_preview_is_the_labelled_placeholder(
    staff_client, product
):
    html = edit_page(staff_client, product)

    assert "images/placeholders/home-assistants.svg" in html
    assert "No image; showing the category placeholder" in html
    assert "Remove image" not in html


def test_the_create_form_has_an_upload_but_no_preview(staff_client):
    html = staff_client.get(reverse("products:manage_product_create")).content.decode()

    assert 'type="file"' in html
    assert "Current image" not in html and "Remove image" not in html


def test_another_fields_error_asks_for_the_file_again(
    staff_client, product_with_image, png_upload
):
    before = product_with_image.image.name

    response = upload_to(staff_client, product_with_image, png_upload, price="0")

    html = response.content.decode()
    assert "This file wasn&#x27;t saved because another field needs attention." in html
    assert "Please select the file again. Any existing image is unchanged." in html
    product_with_image.refresh_from_db()
    assert product_with_image.image.name == before


def test_the_product_list_shows_thumbnails(staff_client, product_with_image, category):
    Product.objects.create(
        name="Seraphine Mini", slug="seraphine-mini", price="99.00", category=category
    )

    html = staff_client.get(reverse("products:manage_products")).content.decode()

    card_url = default_storage.url(images.card_name(product_with_image.image.name))
    assert f'src="{card_url}"' in html
    assert "images/placeholders/home-assistants.svg" in html


# --- import_product_images -----------------------------------------------------


@pytest.fixture
def source(tmp_path):
    """A temporary product-images/ folder."""
    folder = tmp_path / "product-images"
    folder.mkdir()
    return folder


def write_png(folder, filename, width=800, height=1000):
    (folder / filename).write_bytes(_png_bytes(width, height))


def run_import(source, *args):
    out = io.StringIO()
    call_command("import_product_images", "--source", str(source), *args, stdout=out)
    return out.getvalue()


@pytest.fixture
def hush(category):
    return Product.objects.create(
        name="Hush", slug="hush", price="79.00", category=category
    )


def test_the_mapping_names_real_seeded_products():
    from products.management.commands.import_product_images import IMAGE_MAP
    from products.management.commands.seed import CATALOG

    seeded = {entry[0] for entries in CATALOG.values() for entry in entries}
    assert set(IMAGE_MAP) <= seeded
    assert len(IMAGE_MAP) == 12


def test_import_attaches_through_the_upload_path(source, hush):
    write_png(source, "Hush GPT No Text.png")

    output = run_import(source)

    hush.refresh_from_db()
    assert hush.image.name.endswith("/original.png")
    assert folder_files_exist(hush.image.name) == [True, True, True, True]
    assert (hush.image_width, hush.image_height) == (800, 1000)
    assert "Imported          Hush (Hush GPT No Text.png)" in output


def test_import_reports_every_outcome(source, hush, category):
    Product.objects.create(
        name="RecallPro", slug="recallpro", price="1.00", category=category
    )
    Product.objects.create(name="Veil", slug="veil", price="1.00", category=category)
    write_png(source, "Hush GPT No Text.png")
    write_png(source, "Veil GPT Text.png", width=640, height=480)
    write_png(source, "SyncRest GPT Text.png")
    # RecallPro.png is absent; the other nine mapped products don't exist.

    output = run_import(source)

    assert "Missing           RecallPro (RecallPro.png)" in output
    assert (
        "Rejected          Veil (Veil GPT Text.png): This image is 640×480 px. "
        "It must be at least 800 px on its shortest side."
    ) in output
    assert "Please select the file again" not in output
    assert "Unmapped          SyncRest GPT Text.png" in output
    assert "Product not found Seraphine (Seraphine GPT Text.png)" in output
    assert output.strip().endswith(
        "Imported 1 · Skipped 0 · Missing 1 · Rejected 1 · Unmapped 1 · "
        "Product not found 9"
    )
    assert not Product.objects.get(name="Veil").image
    output.encode("cp1252")  # prints on a default Windows console


def test_import_skips_products_that_already_have_an_image(source, hush):
    write_png(source, "Hush GPT No Text.png")
    run_import(source)
    hush.refresh_from_db()
    first = hush.image.name

    output = run_import(source)

    hush.refresh_from_db()
    assert hush.image.name == first
    assert (
        "Skipped           Hush (Hush GPT No Text.png): already has an image" in output
    )


def test_replace_swaps_the_image_and_cleans_up_after_commit(
    source, hush, django_capture_on_commit_callbacks
):
    write_png(source, "Hush GPT No Text.png")
    run_import(source)
    hush.refresh_from_db()
    first = hush.image.name

    with django_capture_on_commit_callbacks(execute=True):
        run_import(source, "--replace")

    hush.refresh_from_db()
    assert hush.image.name != first
    assert folder_files_exist(first) == [False, False, False, False]


def test_a_missing_source_folder_is_an_error(tmp_path):
    with pytest.raises(CommandError, match="Source folder not found"):
        run_import(tmp_path / "nowhere")
