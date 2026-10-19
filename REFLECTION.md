# Reflection


---

## Product Reviews

### Question 1 — Test-Driven Development (TDD)

One behavior I used test-driven development for was updating product reviews without refreshing the entire page. I chose this because I wanted to make sure creating, editing, and deleting reviews would work correctly with HTMX before implementing the feature.

In `reviews/test_htmx.py`, the test `test_a_successful_inline_action_swaps_the_reviews_section_and_summary` checks that these actions return the updated reviews section and rating summary. Initially, all three cases failed because Django returned a `302` redirect instead of the expected `200` response. After implementing the HTMX response in `ReviewActionMixin.finished()` in `reviews/views.py`, the tests passed.

This showed me why TDD is useful. Instead of implementing something and assuming it worked, I had a specific test that identified the problem and confirmed when the behavior was correct.

### Question 2 — Authorization and Deleting Reviews

When a customer attempts to delete a review, Django first checks whether that review belongs to the currently logged-in user.

The delete URL is defined in `reviews/urls.py`, and the request is handled by `ReviewDeleteView` in `reviews/views.py`. The `OwnReviewMixin` uses `Review.objects.own(request.user, self.product)` to find a review associated with both the current user and the product. If a signed-in user does not have a review for that product, Django returns a `404` response; an anonymous visitor is sent to the login page instead.

The `can_delete()` method in `reviews/models.py` also checks that the user is the review's author. If the request is authorized and the customer confirms deletion, `delete_by_author()` removes the review. If the review is currently hidden by staff moderation when it is deleted, the method also creates a restriction to prevent the customer from bypassing moderation by deleting and reposting it.

I think this design is important because customers should have control over their own reviews without being able to modify or delete another person's review.

### Question 3 — HTMX and hx-post

One place I used HTMX is the review form in `templates/reviews/partials/_review_form.html`. The form uses `hx-post="{{ request.path }}"` to submit its information to the existing Django review endpoint without reloading the entire page.

When a customer clicks Edit, HTMX loads the form directly into the product's reviews section. After the customer changes their rating or comment and saves, Django processes the request and returns updated HTML. The `ReviewActionMixin.finished()` method sends back the updated reviews section and rating summary, allowing HTMX to replace those parts of the page.

I tested this myself in the browser by editing my SyncRest review from four stars to five stars. The review and product rating updated without navigating to another page. I also verified that Cancel restored the original review display.

I liked using HTMX here because it made the website feel more interactive while still allowing Django to handle the forms, validation, and authorization.

### Question 4 — Design Decision and Tradeoffs

During my `/grill-me` interview, I had to decide how customers would create, edit, and delete product reviews. The main options were separate Django pages, inline forms without HTMX, or inline forms using HTMX.

I originally chose separate Django pages because they were simpler to implement using Django's built-in class-based views. They also made it easier to handle form validation, errors, and permissions without adding more moving parts. The disadvantage was that customers had to navigate to another page instead of making changes directly on the product page.

Later, while reviewing the assignment requirements, I realized the review actions needed to work with HTMX. I added inline functionality in Phase 7 while keeping the original Django pages as a fallback when JavaScript is unavailable.

This decision required additional templates, response handling, and tests, but it improved the user experience without removing the functionality I had already built. It taught me that software design involves balancing simplicity, maintainability, and user experience, and that an earlier design decision sometimes needs to change when new requirements become clear.

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