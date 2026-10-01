"""Attach the supplied product images to existing products.

Run after ``seed`` (which never imports images). Each mapped file goes
through ``products/images.py`` — the same validation and display copies as a
back-office upload — so a file an employee couldn't upload is rejected here
too, and its product keeps showing the category placeholder.

Products that already have an image are skipped unless ``--replace`` is
given. The source folder, ``product-images/`` by default, is temporary and
never committed.
"""

from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from products import images
from products.models import Product

# Product name -> file in the source folder. Edit a match here.
IMAGE_MAP = {
    "Seraphine": "Seraphine GPT Text.png",
    "Hush": "Hush GPT No Text.png",
    "MindSync": "MindSync GPT 2.png",
    "MindSync Duo": "MindSync Duo.png",
    "RecallPro": "RecallPro.png",
    "MoodSet": "MoodSet GPT No Text.png",
    "DreamWeaver": "DreamWeaver Matrix GPT 3.png",
    "Veil": "Veil GPT Text.png",
    "Calm Collar": "Calm Collar GPT Man.png",
    "CrowdCalm Array": "CrowdCalm Array No Text.png",
    "SyncRest": "SyncRest GPT No Text.png",
    "SoulSear Mark I": "SoulSear No Text.png",
}

OUTCOMES = [
    "imported",
    "skipped",
    "missing",
    "rejected",
    "unmapped",
    "product not found",
]


class Command(BaseCommand):
    help = "Attach the supplied images in product-images/ to existing products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=settings.BASE_DIR / "product-images",
            type=Path,
            help="Folder holding the supplied images (default: product-images/).",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Replace images products already have.",
        )

    def handle(self, *args, source, replace, **options):
        if not source.is_dir():
            raise CommandError(f"Source folder not found: {source}")

        counts = Counter()
        for product_name, filename in IMAGE_MAP.items():
            outcome, detail = self._import(product_name, source / filename, replace)
            counts[outcome] += 1
            line = f"{outcome.capitalize():<17} {product_name} ({filename})"
            if detail:
                line += f": {detail}"
            ok = outcome in ("imported", "skipped")
            self.stdout.write(
                self.style.SUCCESS(line) if ok else self.style.WARNING(line)
            )

        mapped = set(IMAGE_MAP.values())
        for path in sorted(source.iterdir()):
            if path.is_file() and path.name not in mapped:
                counts["unmapped"] += 1
                self.stdout.write(f"{'Unmapped':<17} {path.name}")

        self.stdout.write(
            " · ".join(
                f"{outcome.capitalize()} {counts[outcome]}" for outcome in OUTCOMES
            )
        )

    def _import(self, product_name, path, replace):
        """Return (outcome, detail) for one mapped product."""
        product = Product.objects.filter(name=product_name).first()
        if product is None:
            return "product not found", ""
        if product.image and not replace:
            return "skipped", "already has an image"
        if not path.is_file():
            return "missing", "file not in the source folder"

        try:
            with path.open("rb") as handle:
                processed = images.process_upload(File(handle, name=path.name))
        except ValidationError as error:
            (message,) = error.messages
            return "rejected", message.removesuffix(f" {images.RESELECT_NOTE}")

        product.set_image(processed)
        try:
            with transaction.atomic():
                product.save()
        except Exception:
            images.delete_image_files(product.image.name)
            raise
        return "imported", ""
