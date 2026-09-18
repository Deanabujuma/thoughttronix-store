# Reflection

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