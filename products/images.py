"""Product images: the one path every upload takes.

This is a deliberate deep module. The back-office product form and the
``import_product_images`` command both hand a file to :func:`process_upload`,
which runs every rule in ``prd/product-images.md`` and builds the two WebP
display copies in memory — so a rejected or unprocessable file never touches
storage. :func:`save_image` then writes a fresh folder per upload::

    products/<random-id>/original.<ext>
    products/<random-id>/card.webp
    products/<random-id>/detail.webp

The model stores only the original's name; the copies are its siblings.
:func:`delete_after_commit` removes a folder once the database change that
orphaned it has committed, so a failed save never loses the current image.
"""

import io
import math
import os
import uuid
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import NoReturn

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile, File
from django.core.files.storage import default_storage
from django.db import transaction
from PIL import Image, ImageOps

# Pillow format name -> the extension the original is stored under.
ACCEPTED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MIN_SHORTEST_SIDE = 800
MAX_LONGEST_SIDE = 6000

CARD_BOX = (640, 800)
DETAIL_BOX = (1200, 1500)
WEBP_QUALITY = 80

UPLOAD_DIR = "products"
CARD_FILENAME = "card.webp"
DETAIL_FILENAME = "detail.webp"

UPLOAD_RULES = "JPEG, PNG, or WebP · up to 5 MB · 800–6000 px"
FORMAT_MESSAGE = "Upload a JPEG, PNG, or WebP image."
RESELECT_NOTE = "Please select the file again. Any existing image is unchanged."


@dataclass(frozen=True)
class ProcessedImage:
    """A validated upload and its display copies, not yet in storage."""

    original: bytes
    extension: str
    card: bytes
    detail: bytes
    detail_width: int
    detail_height: int


def process_upload(upload: File) -> ProcessedImage:
    """Validate an uploaded image and build its display copies in memory.

    Checks, in order: file size, format (by content, not extension), pixel
    dimensions, then decodes and resizes. Raises ``ValidationError`` with the
    PRD's message — plus the note to reselect the file — on any failure.
    """
    if upload.size > MAX_UPLOAD_BYTES:
        megabytes = math.ceil(upload.size * 10 / (1024 * 1024)) / 10
        _reject(f"This file is {megabytes:.1f} MB. The maximum is 5 MB.")

    upload.seek(0)
    original = upload.read()
    try:
        image = Image.open(io.BytesIO(original))
    except Image.DecompressionBombError:
        _reject(
            f"This image is too large. It must be at most {MAX_LONGEST_SIDE} px "
            "on its longest side."
        )
    except (OSError, ValueError):
        _reject(FORMAT_MESSAGE)

    with image:
        if image.format not in ACCEPTED_FORMATS:
            _reject(FORMAT_MESSAGE)
        width, height = image.size
        if min(width, height) < MIN_SHORTEST_SIDE:
            _reject(
                f"This image is {width}×{height} px. It must be at least "
                f"{MIN_SHORTEST_SIDE} px on its shortest side."
            )
        if max(width, height) > MAX_LONGEST_SIDE:
            _reject(
                f"This image is {width}×{height} px. It must be at most "
                f"{MAX_LONGEST_SIDE} px on its longest side."
            )
        try:
            image.load()  # the first frame, for animated WebP
            upright = _display_ready(image)
            card, _ = _webp_copy(upright, CARD_BOX)
            detail, detail_size = _webp_copy(upright, DETAIL_BOX)
        except (OSError, ValueError):
            _reject(f"This image couldn't be read; it may be damaged. {FORMAT_MESSAGE}")

    return ProcessedImage(
        original=original,
        extension=ACCEPTED_FORMATS[image.format],
        card=card,
        detail=detail,
        detail_width=detail_size[0],
        detail_height=detail_size[1],
    )


def save_image(processed: ProcessedImage) -> str:
    """Write a processed image to a new folder; return the original's name."""
    folder = PurePosixPath(UPLOAD_DIR, uuid.uuid4().hex)
    name = default_storage.save(
        str(folder / f"original.{processed.extension}"),
        ContentFile(processed.original),
    )
    default_storage.save(str(folder / CARD_FILENAME), ContentFile(processed.card))
    default_storage.save(str(folder / DETAIL_FILENAME), ContentFile(processed.detail))
    return name


def card_name(original_name: str) -> str:
    """Storage name of the catalog-card copy that sits beside an original."""
    return str(PurePosixPath(original_name).with_name(CARD_FILENAME))


def detail_name(original_name: str) -> str:
    """Storage name of the detail-page copy that sits beside an original."""
    return str(PurePosixPath(original_name).with_name(DETAIL_FILENAME))


def delete_image_files(original_name: str) -> None:
    """Delete an original, both copies, and their emptied folder.

    Missing files are ignored: a leftover file is better than an error for
    the employee.
    """
    for name in (original_name, card_name(original_name), detail_name(original_name)):
        try:
            default_storage.delete(name)
        except OSError:
            pass
    try:
        os.rmdir(default_storage.path(str(PurePosixPath(original_name).parent)))
    except (NotImplementedError, OSError):
        pass  # storage without folders, or the folder isn't empty


def delete_after_commit(original_name: str) -> None:
    """Delete an image's files once the current transaction commits.

    If the transaction rolls back, nothing is deleted.
    """
    if original_name:
        transaction.on_commit(lambda: delete_image_files(original_name))


def _reject(message: str) -> NoReturn:
    raise ValidationError(f"{message} {RESELECT_NOTE}", code="invalid_image")


def _display_ready(image: Image.Image) -> Image.Image:
    """Upright, in a mode WebP can store, keeping any transparency."""
    upright = ImageOps.exif_transpose(image)
    has_alpha = upright.mode in ("RGBA", "LA", "PA") or (
        upright.mode == "P" and "transparency" in upright.info
    )
    return upright.convert("RGBA" if has_alpha else "RGB")


def _webp_copy(image: Image.Image, box: tuple[int, int]) -> tuple[bytes, tuple]:
    """Shrink to fit ``box`` (never enlarge) and encode as metadata-free WebP."""
    copy = image.copy()
    copy.thumbnail(box, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    copy.save(buffer, "WEBP", quality=WEBP_QUALITY)
    return buffer.getvalue(), copy.size
