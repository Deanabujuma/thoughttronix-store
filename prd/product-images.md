# PRD: The ThoughtTronix Store — Product Images

*Settled in a design interview on 2026-09-30. Extends `prd/core-platform.md`; where the two disagree, this document wins for product images only.*

---

## Problem Statement

Every product shows a static category placeholder (`Category.placeholder_image`). The store has real product artwork in `product-images/` (13 PNGs, 1.6–2.4 MB, mostly 1122×1402 portrait posters) and no way to upload, validate, or display it.

## Requirements

- Employees upload product images through the back office.
- The catalog and product detail pages show a product's image when available, otherwise its existing category placeholder.
- Unusable uploads are rejected before saving, with a clear explanation.

## Decisions

### Model and storage

| # | Decision |
|---|----------|
| Q1 | **One optional image per product.** `Product` gains `image`, `image_alt`, and the detail copy's `image_width` / `image_height`. No gallery. |
| Q6 | Django's **local media storage**: `MEDIA_ROOT = BASE_DIR / "media"`, `MEDIA_URL = "/media/"`. `media/` is gitignored; Django serves it only when `DEBUG` is True. The README notes that production needs its own media serving. |
| Q18 | Each upload gets its own folder: `products/<random-id>/original.<ext>`, `card.webp`, `detail.webp`. `<ext>` comes from the format Pillow detects, not the uploaded name. A new upload never overwrites a file in use, and a new URL means no stale browser cache. |
| Q8 | The old folder (original and both copies) is deleted **only after the database change commits** (`transaction.on_commit`): on replace, on clear, and on product delete, including bulk deletes such as `seed`'s. A failed upload or save leaves the existing image and its files untouched. *(Amended during build: the emptied `products/<random-id>/` folder is removed too, since deleting files alone left empty folders behind.)* |
| Q16 | Validation, processing, and cleanup live in **`products/images.py`**, a third deep module with docstrings and type hints. The product form and the import command both go through it. |

### Validation

All checks run before anything is saved. Every rejection also says the file must be selected again and that the existing image is unchanged.

| # | Decision |
|---|----------|
| Q2 | **JPEG, PNG, WebP only**, judged by the contents Pillow detects, not the extension. Unsupported or corrupt → *"Upload a JPEG, PNG, or WebP image."* |
| Q3 | **5 MB maximum** (named constant) → *"This file is 7.3 MB. The maximum is 5 MB."* |
| Q4 | **At least 800 px on the shortest side, at most 6000 px on the longest** (named constants). The message states the image's dimensions and the violated limit, e.g. *"This image is 640×480 px. It must be at least 800 px on its shortest side."* |
| Q14 | A new file **and** *Remove image* together → *"Choose a new image or tick Remove image, not both. If uploading, please select the file again."* |

### Processing

| # | Decision |
|---|----------|
| Q7 | Keep the original; generate two **WebP copies at quality 80**: **card** within 640×800 and **detail** within 1200×1500. Proportions kept, never cropped, never enlarged. Copies are built **during validation**, so a processing failure is a validation error and the existing image survives. *(Amended during build: a file that opens as JPEG/PNG/WebP but can't be decoded gets* "This image couldn't be read; it may be damaged. Upload a JPEG, PNG, or WebP image." *)* |
| Defaults | EXIF orientation is applied to the copies; the copies carry no metadata (the original is stored as uploaded and never linked); transparency is preserved; animated WebP uses its first frame. |

### Display

| # | Decision |
|---|----------|
| Q5 | Catalog cards use a fixed **4:5 frame** with `object-contain` on a DaisyUI theme background (e.g. `bg-base-300`). Placeholders sit in the same frame. The detail page shows the whole image at its own proportions, uncropped. *(Amended during build: the frame has a 1 px `border-base-content/15` border, because the letterboxing was invisible on the dark theme and images looked different heights. The image is positioned out of flow (`absolute inset-0`), and the catalog link gets `shrink-0 basis-full`, so neither the image's natural size nor the card's flex layout can resize the frame.)* |
| Q12 | Catalog images `loading="lazy"`; the detail image loads immediately with the stored `width` / `height`. |
| Q15 | Alt text: `image_alt` if set, else *"Product image of {name}"*. A placeholder **always** uses the category placeholder description, e.g. *"Neural Implants category placeholder (no product photo yet)"*. Help text on `image_alt` asks for the scene and any important words printed in the image. |
| Review | **Missing files fall back.** If a product has an image but the copy a page needs is missing from storage, that page shows the category placeholder (with placeholder alt text) instead of a broken image. |

### The back office

| # | Decision |
|---|----------|
| Q13 | The product form shows the current image (or the labelled placeholder) in the catalog frame, a **Remove image** checkbox, and a DaisyUI `file-input` with `accept="image/jpeg,image/png,image/webp"`. Help text states the rules up front: *JPEG, PNG, or WebP · up to 5 MB · 800–6000 px*. The product list gains a thumbnail column. *(Amended during build: when a different field fails, a chosen file is discarded by the browser, so the image field then says* "This file wasn't saved because another field needs attention." *plus the reselect note. The Django admin shows the image fields read-only, so every upload goes through validation.)* |

### Build

| # | Decision |
|---|----------|
| Build | *(Amended during build.)* The catalog frames need new Tailwind classes, but Windows Smart App Control blocked the unsigned `tailwind-cli-extra` binary, so the CSS couldn't be rebuilt. The build now uses the official Tailwind Labs standalone CLI, pinned to **v4.3.2** (`TAILWIND_CLI_USE_DAISY_UI = False`), with DaisyUI's official plugin file vendored at `assets/css/daisyui.mjs`, pinned to **v5.7.47**. `source.css` excludes that file from class scanning (`@source not`), so only the classes the templates use are generated. Security settings stay on; the generated `tailwind.css` is never hand-edited. |

### The supplied images

| # | Decision |
|---|----------|
| Q9 | A separate **`import_product_images`** command attaches them to existing products through the same validation and processing. `product-images/` stays temporary, uncommitted, and gitignored. `seed` does not import images. |
| Q10 | Mapping (a dict at the top of the command): Seraphine → `Seraphine GPT Text.png`; Hush → `Hush GPT No Text.png`; MindSync → `MindSync GPT 2.png`; MindSync Duo → `MindSync Duo.png`; RecallPro → `RecallPro.png`; MoodSet → `MoodSet GPT No Text.png`; DreamWeaver → `DreamWeaver Matrix GPT 3.png`; Veil → `Veil GPT Text.png`; Calm Collar → `Calm Collar GPT Man.png`; CrowdCalm Array → `CrowdCalm Array No Text.png`; SyncRest → `SyncRest GPT No Text.png`; SoulSear Mark I → `SoulSear No Text.png`. |
| Q11 | Products that already have an image are **skipped** unless `--replace` is given. The summary counts **imported, skipped, missing, rejected, unmapped**, and **product not found**. `SyncRest GPT Text.png` is reported as unmapped, not as an error. |

### Tests

| # | Decision |
|---|----------|
| Q17 | Test images are generated in memory with Pillow in `conftest.py` fixtures, including exact boundaries (799 vs 800 px, 5 MB + 1 byte). An **autouse fixture points `MEDIA_ROOT` at `tmp_path`** for every test, including the `seed` tests in `products/tests.py`. The import command is tested against a temporary source folder. Missing-file fallback is tested on the catalog and detail pages. The false "tests never invoke the seed command" line is removed from the `conftest.py` docstring. |

## Out of Scope

Multiple images per product, cropping tools, client-side previews or JavaScript, SVG/HEIC/AVIF/GIF uploads, cloud storage, regenerating copies for existing uploads, importing images from `seed`.
