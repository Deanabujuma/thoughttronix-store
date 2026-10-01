# Reflection

## Product Images

### Question 1 — Interview decision

During the grill-me interview, Claude recommended importing the supplied images through the seed command. I chose a separate `import_product_images` command because I wanted to attach images without resetting the demo database. This kept importing images separate from recreating products. The command skips products that already have an image unless I use `--replace`.

### Question 2 — Upload code

The image field is in `products/models.py`, line 101:

```python
image = models.ImageField(max_length=200, blank=True)
```

`blank=True` allows a product to have no uploaded image, so it can use its category placeholder. This field does not specify `upload_to`. Normally, `upload_to` determines the upload path within media storage. In my implementation, `save_image()` in `products/images.py` builds a separate folder for each upload, using `products/<random-id>/`.

The opening upload form tag is in `templates/products/manage_product_form.html`, line 13:

```html
<form method="post" enctype="multipart/form-data" class="mt-2 space-y-4">
```

`enctype="multipart/form-data"` allows the browser to send the image file along with the other form fields. Django receives uploaded files through `request.FILES`.

### Question 3 — Following Lucent’s image

I created Lucent through the back-office product form and uploaded its headband image.

The original image is stored on disk at:

```text
C:\Users\deana\cidm3312\thoughttronix-store\media\products\ce78b0f89de240538a46829add3bae46\original.png
```

`MEDIA_ROOT = BASE_DIR / "media"` in `config/settings.py`, line 146, determines the main storage directory. The code in `products/images.py` creates the product’s random folder and filenames.

The value stored in the database’s Product image field is:

```text
products/ce78b0f89de240538a46829add3bae46/original.png
```

The database stores a relative file path rather than the image itself.

The browser requests this image on Lucent’s detail page:

```text
http://127.0.0.1:8000/media/products/ce78b0f89de240538a46829add3bae46/detail.webp
```

`MEDIA_URL = "/media/"` in `config/settings.py`, line 144, supplies the URL prefix. The detail page uses the processed `detail.webp` copy instead of the original PNG. The catalog uses `card.webp`.

In `config/urls.py`, line 25, this code connects media URLs to the files on disk:

```python
static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

During development, Django serves files from `MEDIA_ROOT` through these URLs. This helper adds no media routes when `DEBUG` is False, so production needs separate media serving.

## Discount Coupons

### Question 1

I was confused about whether a product-specific coupon would discount the whole cart or just the selected products. I asked Claude to clarify that. I decided that a code like HUB15 should discount Seraphine products only, so other items in the cart stay at their regular price.

### Question 2

When I reviewed checkout in the browser, I noticed that applying a code locked the coupon box. To try another code, I had to remove the first one. I wanted customers to be able to switch codes directly, so I asked Claude to make the box editable after applying a code. I tested it by replacing one code with HUB15 and then trying the expired SUMMER20. The valid code changed the discount, and the expired code showed an error without keeping the previous discount. One existing test, test_the_form_declares_no_imperative_validation, failed because the first version added a clean_coupon_code method to CheckoutForm. Claude moved coupon validation to a separate CouponForm, and the test suite passed afterward.

## Featured Products

### Question 1 - Trace the feature

The featured products feature starts in the Django admin. When I check the Featured box for a product and save it, Django stores `True` in the product's `is_featured` field. That field was added to the `Product` model in `products/models.py` as a BooleanField with a default of `False`.

The database was updated through the migration in `products/migrations/0003_product_is_featured.py`. The storefront templates then check the value of `product.is_featured`. In `templates/products/catalog.html`, the Featured badge appears on the product card when the value is true. The same check is also used in `templates/products/detail.html`, so the badge appears on the individual product page too.

### Question 2 - How I verified it

I used the Django admin interface to mark Seraphine, SoulSear Mark I, and SoulSear Mark II as featured.

I then opened the storefront catalog and confirmed that the Featured badge appeared for the products I marked and not for the other products. I also opened the individual product detail pages and confirmed that the Featured badge appeared there too.

Finally, I ran `uv run pytest` in the terminal. All 166 tests passed.

### Question 3 - Judgement

One thing that confused me was that after the badge code was added, I initially did not see the Featured badge on the storefront. At first I was looking at the regular storefront and expected to be able to edit the product there, but the storefront only allows shopping actions such as adding products to the cart.

I realized that I needed to use Django admin instead. I first entered the admin while signed in as the employee account, which did not have permission to edit anything. I then logged in with the admin account, opened the Products section, and marked the required products as featured.

After saving the products and returning to the storefront, the Featured badge appeared correctly. This helped me understand the difference between the customer-facing storefront, staff access, and Django's admin interface.