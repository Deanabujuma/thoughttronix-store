# Reflection

## Account Security Center

### Question 1 — Review One Phase

I chose Phase 4, which focused on completing the password reset feature. The goal was to let users open a reset link, create a new password, and sign back into their accounts.

When I tested this phase in my browser, I ran into an issue because the reset link kept showing as invalid. After investigating, I found out that the email formatting was splitting the link into two lines. Once I removed the extra formatting character and combined the link correctly, the password reset form worked.

I also tested a weak password, which the system rejected because it was too common and entirely numeric. Then I created a stronger password and successfully signed in. I confirmed that my previous password no longer worked and that the reset link couldn't be reused. After seeing these results, I felt comfortable approving Phase 4 and moving on to Phase 5.

### Question 2 — Authentication Code Versus the Lesson

Two Django authentication components used in my project are `LoginRequiredMixin` and `AuthenticationForm`.

`LoginRequiredMixin` appears in `accounts/views.py`, where `SecurityView` uses it to require users to sign in before accessing the Security page. When I tested this, the application redirected me to login if I wasn't authenticated.

`AuthenticationForm` appears in `accounts/forms.py`, where `SignInForm` inherits from it. Django handles the login credential validation, while my project adds DaisyUI styling.

These components follow the authentication approach from the lesson because they use Django's built-in security features rather than implementing my own login system.

### Question 3 — Password Management Versus the Lesson

I chose the password reset feature. In `accounts/views.py`, `PasswordResetSetView` uses Django's `PasswordResetConfirmView`. The password reset form uses Django's `SetPasswordForm`, with custom styling to match the website.

Django handles important security features such as checking reset tokens and validating new passwords. I tested these protections by attempting to use a weak password and by opening a reset link after it had already been used.

This approach matches the lesson because I relied on Django's built-in password management instead of creating my own security-sensitive logic. My project also sends a password-change notification through the console email backend and redirects users to login after a successful reset.

### Question 4 — The Tracer-Bullet Plan

I chose Phase 3 because it demonstrated why dividing the implementation into smaller phases was useful.

By the end of Phase 3, users could click Forgot Password, submit an email address, and generate a password reset email in the terminal. The application showed the same confirmation message whether the email was registered or not, which helped protect account privacy.

At this point, the reset link opened a temporary page to verify its validity, but users couldn't change their passwords yet. That functionality was implemented in Phase 4.

This was a useful stopping point because I could verify that password reset requests and email generation worked before adding the actual password-changing process. It made reviewing the feature easier and helped separate issues with generating reset links from issues with setting a new password.

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