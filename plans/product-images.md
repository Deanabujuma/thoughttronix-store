# Implementation Plan: The ThoughtTronix Store — Product Images

*Companion to `prd/product-images.md`. The PRD owns the decisions; this plan owns the sequence. The suite is green at every phase boundary.*

---

## Phase 0 — Prep

1. `uv add pillow`, which updates `pyproject.toml` and `uv.lock`.
2. `MEDIA_ROOT` / `MEDIA_URL` in settings; root urls serve media only when `DEBUG` is True. Add `media/` and `product-images/` to `.gitignore`.
3. `conftest.py`: an autouse fixture setting `MEDIA_ROOT` to `tmp_path`; in-memory Pillow image fixtures; remove the false "tests never invoke the seed command" line from the docstring.

**Verification.** The full suite passes, and the `seed` tests leave nothing in the real `media/`.

## Phase 1 — Tracer Bullet: Upload One Valid Image, See It Everywhere

1. `products/images.py`: validate a file, build both WebP copies in memory, save a new `products/<random-id>/` folder, and delete a folder. Limits are named constants. Update the architecture statement in `CLAUDE.md` from two deep modules to three.
2. `Product` fields `image`, `image_alt`, `image_width`, `image_height` plus a migration. Model properties give the card URL, detail URL, and alt text, falling back to the placeholder when there is no image **or the needed copy is missing from storage**.
3. `ProductForm` gains the image fields; the form gets `enctype="multipart/form-data"`; `StyledModelForm` gives file inputs `file-input`.
4. Catalog cards: 4:5 frame, `object-contain`, `loading="lazy"`. Detail page: whole image with stored `width` / `height`, loaded immediately.

**Out of bounds:** rejection messages beyond "valid image accepted", replace/clear/delete cleanup, the back-office preview, the import command.

## Phase 2 — Validation and Messages

Format by content, 5 MB, 800 / 6000 px, processing failures, and the Remove-plus-file conflict. Each message is the PRD's exact wording plus the "select the file again; existing image unchanged" note. Boundary tests for every rule.

## Phase 3 — File Lifecycle

Replace, clear, and product delete remove the old folder via `transaction.on_commit`, using a `post_delete` receiver so bulk deletes (`seed`) are covered. Tests show that a failed save keeps the old files, and that a rolled-back transaction deletes nothing.

## Phase 4 — Back-Office Upload Experience

A preview of the current image or labelled placeholder in the catalog frame, a Remove image checkbox, `accept`, the rules help text, `image_alt` help text, and a thumbnail column on the product list.

## Phase 5 — `import_product_images`

The mapping dict, skip unless `--replace`, and the summary of imported / skipped / missing / rejected / unmapped / product not found, all running through `products/images.py`. Tested against a temporary source folder.

## Phase 6 — Docs

A README note on media in production and on running `import_product_images` after `seed`. The `PROMPTS.md` entry for the build session is written after review.
