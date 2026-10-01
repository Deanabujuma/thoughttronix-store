# The ThoughtTronix Store

*Your Thoughts, Our Business.*

A server-rendered Django 6 storefront and back office for the world's most
beloved consumer neural technology: browse the catalog, fill a cart, check
out through a fully validated form, and — if you're staff — run the store
from the back office, analytics dashboard included.

## Getting started

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/). No Node.js —
Tailwind runs as the official standalone CLI (v4.3.2, downloaded on first
use), with DaisyUI loaded from its pinned plugin file,
`assets/css/daisyui.mjs` (v5.7.47). The official CLI is used because
Windows Smart App Control blocks the unsigned DaisyUI-bundling fork.

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed
uv run python manage.py tailwind runserver
```

Then open <http://127.0.0.1:8000/>. From clone to browsing the store, this
takes about two minutes.

## Demo logins

The `seed` command creates a fixed demo world — the same one every run:

| Username   | Password      | Who they are                                                  |
| ---------- | ------------- | ------------------------------------------------------------- |
| `admin`    | `admin123`    | Superuser: everything below, plus the Django admin at `/admin/` |
| `employee` | `employee123` | Staff: the back office (products, orders, dashboard)           |
| `customer` | `customer123` | A customer with order history and a live cart                  |

## Commands

| Command                                     | What it does                             |
| ------------------------------------------- | ---------------------------------------- |
| `uv sync`                                    | Install dependencies                     |
| `uv run python manage.py migrate`            | Apply database migrations                |
| `uv run python manage.py seed`               | Reset the database to the demo world (destructive, idempotent) |
| `uv run python manage.py import_product_images` | Attach the supplied images in `product-images/` to products (run after `seed`; `--replace` overwrites) |
| `uv run python manage.py tailwind runserver` | Dev server + Tailwind watch              |
| `uv run python manage.py tailwind build`     | Compile production CSS                   |
| `uv run python manage.py tailwind build --force` | Recompile CSS after changing classes in templates (a plain build only notices changes to `source.css`) |
| `uv run pytest`                              | Run the test suite                       |
| `uv run ruff check .`                        | Lint                                     |
| `uv run ruff format .`                       | Format                                   |

## Product images

Staff upload product images from the back office product form: JPEG, PNG,
or WebP, up to 5 MB, 800–6000 px. Each upload keeps its original plus two
WebP display copies in `media/` (gitignored). Products without an image
show their category's placeholder.

`seed` never imports images and removes the images of the products it
wipes. To give the demo products their pictures, place the supplied images
in `product-images/` (temporary, never committed) and run
`import_product_images` after `seed`.

Django serves `media/` only while `DEBUG` is True. A production deployment
needs its own media serving (a web server or a storage service).

## Repo layout

`config/` is the project package (settings, root URLs); the four apps are
`accounts` (custom user model), `products` (the public catalog and its
back-office CRUD, with image handling in `products/images.py`), `orders`
(cart, checkout, orders — with the `place_order` service in
`orders/services.py`), and `dashboard` (staff analytics, with the
aggregations in `dashboard/queries.py`). Project-level
templates live in `templates/`, static sources in `assets/`. The product
requirements are in `prd/`, the phase-by-phase build plan in `plans/`, and
`PROMPTS.md` is where AI usage on this codebase gets logged.
