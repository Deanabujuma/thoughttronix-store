# ThoughtTronix Codebase Map

## 1. The Apps and What Each Owns

### accounts
The `accounts` app handles users, login, logout, signup, and staff access. It uses a custom `User` model that extends Django's built-in user model and adds an optional `job_title` field.

### products
The `products` app handles the store catalog. It owns the `Category`, `Product`, and `Tag` models, along with product pages, category pages, searching, filtering, and the staff product management screens.

### orders
The `orders` app handles the shopping and checkout side of the store. It manages carts, cart items, checkout, customer orders, order history, and staff order management.

### dashboard
The `dashboard` app handles the staff analytics page. It calculates things such as revenue, order count, average order value, revenue over time, and top-selling products by reading information from the orders in the database.

## 2. The Path of One Request

When a browser requests the home page at `/`, Django first checks `config/urls.py`. Several apps are included at the root, but the empty URL pattern in `products/urls.py` is the one that matches `/`.

That URL sends the request to `CatalogView` in `products/views.py`. `CatalogView` gets the products from the database and provides them to `templates/products/catalog.html`. The catalog template also uses `templates/base.html` for the shared page layout.

The basic path is:

`config/urls.py` → `products/urls.py` → `CatalogView` in `products/views.py` → `templates/products/catalog.html`

## 3. A Model I Read

I looked at the `Cart` model in `orders/models.py`. It represents a customer's shopping cart and contains methods for adding products, getting the cart's items, and counting how many total units are in the cart.

One method I found interesting was `item_count()`. Instead of only counting the number of different cart rows, it adds the quantities together. For example, if a customer has two of one product and one of another product, the cart count is three instead of two.

## 4. Deleting a Category

A Category cannot be deleted if Products still belong to it. Django blocks the deletion and raises a `ProtectedError`, leaving both the Category and its Products unchanged.

The code that controls this behavior is in the `Product.category` ForeignKey in `products/models.py`:

```python
category = models.ForeignKey(
    Category,
    on_delete=models.PROTECT,
    related_name="products",
)
The important part is on_delete=models.PROTECT. This tells Django to protect the Category from being deleted while Products still reference it.

5. Where the Tests Live

The tests are organized throughout the project close to the apps and features they test. There are test files in apps such as accounts, products, orders, and dashboard, and the project uses pytest to run them.

The project-level conftest.py contains shared pytest fixtures. I understand fixtures as reusable test data or setup that different tests can request when they need it. For example, a fixture can create a customer, product, cart, or other object so that every test does not have to recreate the same setup from scratch.

6. One Thing I'm Still Working to Understand

One part that took me more work to understand was how the cart prevents duplicate CartItem rows when the same product is added more than once.

I asked Claude to walk me through the code and looked at the Cart.add() method and the CartItem model in orders/models.py. I learned that Cart.add() uses get_or_create() to look for an existing row for that product. If the product is already in the cart, it increases the quantity instead of creating another row.

I also learned that there is a database UniqueConstraint on the combination of cart and product. This gives the cart a second layer of protection because the database will not allow two separate rows for the same product in the same cart.

I understand the main idea now, although I am still getting used to how Django model methods and database constraints work together to enforce the same rule.