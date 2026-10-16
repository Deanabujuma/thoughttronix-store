# PRD: The ThoughtTronix Store — Wishlist

*Settled in a design interview on 2026-10-16. Extends `prd/core-platform.md`; where the two disagree, this document wins for the wishlist only.*

---

## Problem Statement

A ThoughtTronix shopper who finds a product they like but aren't ready to buy has nowhere to keep it. Their only option is the cart, but the cart is for buying: it's meant to be checked out, and everything in it shows up at checkout. So shoppers either clutter their cart with things they're only thinking about, or they lose track of the product and have to search the catalog for it again later. Nothing in the store lets them say "I want this, just not yet."

## Solution

Every signed-in shopper gets one private wishlist.

On a product's detail page, next to "Add to cart", a **Save to wishlist** button saves the product without reloading the page. The button immediately changes to **Saved — remove**, and clicking it again removes the product, also without a reload. The button always shows whether this product is in the shopper's wishlist.

A new **Wishlist** page, linked from the navbar, lists everything the shopper has saved, newest first, with each product's image, name, price and availability, and a link back to its page. When nothing is saved yet, the page shows a designed empty state instead of a blank list.

Each wishlist belongs to one person. Nobody else using the storefront can see or change it, and employees have no back-office screen for it. Signed-out visitors see the same button as a link that takes them to sign in and then back to the product.

Products that are no longer for sale can't be newly saved, but anything already saved stays in the wishlist and can always be removed.

## User Stories

**Visitor (signed out)**

1. As a visitor, I want to see a "Save to wishlist" option on a product page, so that I know the store has wishlists.
2. As a visitor, I want clicking "Save to wishlist" to take me to the sign-in page and then back to the same product, so that I can save it as soon as I've signed in.
3. As a visitor, I want to have no access to any wishlist, so that the feature never exposes anyone's saved products.

**Signed-in shopper (customer, employee, or admin)**

4. As a shopper, I want to save a product to my wishlist from its detail page without the page reloading, so that I can keep browsing where I was.
5. As a shopper, I want the button to change to "Saved — remove" right after I save, so that I know the save worked.
6. As a shopper, I want to remove a saved product from its detail page without the page reloading, so that I can change my mind quickly.
7. As a shopper, I want the button to change back to "Save to wishlist" right after I remove, so that I know the removal worked.
8. As a shopper, I want the button to show whether the product is saved every time I open its page, so that I don't have to remember.
9. As a shopper, I want saving a product twice (a double-click, or two open tabs) to keep just one copy, so that my wishlist never has duplicates.
10. As a shopper, I want removing a product that's already gone to cause no error, so that a double-click or a stale tab never breaks anything.
11. As a shopper, I want the button to always show my wishlist's real state after any click, so that it never disagrees with what's saved.
12. As a shopper, I want to be unable to save a product that isn't for sale, so that my wishlist matches what the store sells, the same as my cart.
13. As a shopper, I want a product I saved to stay in my wishlist if it later becomes unavailable, so that I don't silently lose it.
14. As a shopper, I want to be able to remove a saved product even after it becomes unavailable, so that I'm never stuck with an item I can't delete.
15. As a shopper, I want an unavailable product I haven't saved to show a disabled "Save to wishlist" button, so that it's clear I can't save it, while the add-to-cart button's "Unavailable" explains why and the page doesn't show two identical "Unavailable" buttons.
16. As a shopper, I want a "Wishlist" link in the navbar, so that I can find my saved products from any page.
17. As a shopper, I want my wishlist page to list my saved products newest first, so that what I saved most recently is at the top.
18. As a shopper, I want each saved product on the page to show its image, name, price and availability, and to link to its detail page, so that I can decide what to do next.
19. As a shopper, I want a designed empty state when I haven't saved anything, so that the page explains itself instead of looking broken.
20. As a shopper, I want only my own saved products on my wishlist page, so that my choices stay private.
21. As a shopper, I want no one else using the storefront to be able to see, add to, or remove from my wishlist, so that it's truly mine.
22. As a shopper, I want a product deleted from the store to disappear from my wishlist, so that my list never shows something that no longer exists.
23. As an employee or admin, I want my own private wishlist too, so that I can shop and test the storefront the same way customers do.
24. As a shopper using a screen reader, I want the button to announce whether the product is saved, so that I know its state without seeing the heart icon.

**Admin**

25. As an admin, I want to view and manage wishlists in the Django admin, the same way I can with carts, so that I can do direct data management when something needs fixing.

**Employee**

26. As an employee, I want no wishlist screen in the back office, so that customers' private wishlists stay out of everyday staff tools.

**Developer**

27. As a developer, I want the demo `customer` login to have a wishlist after `seed`, including one saved product that's unavailable, so that every button state and the list page can be shown right away.
28. As a developer, I want `seed` to remove all wishlists before rebuilding, and to give the demo wishlist the same order on every run, so that the demo world stays repeatable.
29. As a developer, I want viewing a product page or the wishlist page to never create a wishlist, so that browsing doesn't fill the database with empty rows.

## Implementation Decisions

### A new `wishlist` app

- A new Django app with the namespace `wishlist`, with its own templates and partials following the template conventions. It's kept separate from the cart and checkout code, the same way the dashboard has its own app.
- No new service module: the project's three deliberate deep modules stay as they are. The wishlist's logic lives in its models, and its views stay thin.

### Models

- **Wishlist:** one per user through a one-to-one link to the user (deleting the user deletes it). It's created only when needed, through a `for_user` class method that mirrors `Cart.for_user`.
- **WishlistItem:** links a wishlist (cascade) to a product (cascade) and records when it was added (`added_at`). A unique constraint on the wishlist–product pair, named in the same style as the cart's, makes duplicates impossible.
- Model methods carry the behavior:
  - saving is a get-or-create, so saving twice keeps one row
  - removing deletes the row if it exists and is harmless if it doesn't
  - a **read-only** "has this user saved this product?" check answers false for a user with no wishlist and never creates one
- Deleting a product removes it from every wishlist. A product that is only marked unavailable stays saved.

### Views and URLs (`wishlist:` namespace)

- `wishlist:save` at `wishlist/save/<product pk>/` and `wishlist:remove` at `wishlist/remove/<product pk>/`. The pk identifies the **product**, not a wishlist item, following add-to-cart's pk URL. Both are POST-only, so a GET is refused.
- Both views use `LoginRequiredMixin` and share a small base view that performs the action and re-renders the button partial with the true saved state, in the style of the cart's shared line-action view.
- **Save** looks the product up through `Product.objects.available()`, so an unavailable or unknown product returns 404, the same as add-to-cart. Only save creates a wishlist, through `for_user`.
- **Remove** looks the product up among all products, so an item that became unavailable can still be removed. It acts only on the signed-in user's own wishlist.
- Every lookup goes through the signed-in user, never another user's data, so no request can read or change someone else's wishlist.
- `wishlist:list` at `/wishlist/`: a `LoginRequiredMixin` list view showing only the signed-in user's items, newest first, with their products loaded efficiently. It is read-only and never creates a wishlist; a user without one sees the empty state.
- Every signed-in user (customer, staff, admin) can use the wishlist. No role checks are added, matching the cart.
- Signed-out POSTs to save or remove are redirected to login and change nothing. As with add-to-cart, an HTMX request whose session expired mid-page isn't specially handled.

### Product detail page

- `ProductDetailView` adds a `saved` boolean to its context for signed-in users, using the read-only model check: one small query, on this page only. There is no wishlist context processor.
- The detail template includes the wishlist button partial next to the add-to-cart button and passes it `saved`, the same way the add-to-cart partial receives `in_cart`.

### The wishlist button partial

- An HTMX partial (`hx-post`, `hx-swap="outerHTML"`) that replaces only itself. There's no out-of-band swap and no navbar update. The CSRF token comes from the header `base.html` already sets on every HTMX request.
- States:

| State | Label | Style | Behavior |
|---|---|---|---|
| Signed out | ♡ Save to wishlist | button-styled link | goes to the login page with `next` set to the current product page |
| Available, not saved | ♡ Save to wishlist | outlined secondary button | posts to save; `aria-pressed="false"` |
| Saved (available or not) | ♥ Saved — remove | filled secondary button | posts to remove; `aria-pressed="true"` |
| Unavailable, not saved | ♡ Save to wishlist | outlined, disabled | never posts |

### Navbar and list page

- A plain "Wishlist" link in the navbar for signed-in users, alongside Orders, Addresses and Security. It has no count badge.
- The list page extends `base.html` and shows each saved product's image, name, price, availability and a link to its detail page. Removing happens on the detail page. The page has a designed empty state.
- Tailwind and DaisyUI classes only, with no JavaScript beyond HTMX.

### Django admin and back office

- `Wishlist` is registered in the Django admin with a `WishlistItem` inline and search by username, mirroring the cart's admin. Only admin users with the needed permissions can manage wishlist data.
- No back-office (employee) wishlist screen.

### Seed

- A `CUSTOMER_WISHLIST` constant, mirroring `CUSTOMER_CART`, lists two or three available products and one unavailable product for the demo `customer` login.
- A `_create_customer_wishlist()` step builds it with fixed `added_at` times, so the newest-first order is the same on every run.
- `_wipe()` explicitly deletes all wishlists alongside the carts.
- The seed's success message and the README mention the demo wishlist.
- `seed` is exercised only through the test suite's isolated database. It is never run against the developer's own database during implementation.

### Testing

- Follows the project's testing conventions: pytest and pytest-django, with shared plain fixtures (for example a second customer, an unavailable product, a saved item) in the project-level conftest.
- Tests are organized by topic in the wishlist app:
  - **Models:** `for_user` creates once; the read-only check never creates; the unique constraint; saving twice keeps one row; removing a missing item is harmless; deleting a product or user cascades; an unavailable product stays saved.
  - **Views:** save and remove return the partial (not a full page) in the correct state; saving an unavailable product returns 404; removing an unavailable saved product works; signed-out requests redirect and change nothing; GET is refused; staff and admin can save.
  - **Privacy:** one user's actions never touch another user's wishlist; the list page shows only your own items; the detail page's `saved` flag is per-user.
  - **List page:** newest first; image, name, price, availability and link; empty state; viewing creates no wishlist; the navbar link appears only when signed in.
- The existing seed tests are extended (the demo wishlist and its fixed order, the wipe, repeatability), and the product detail tests cover all four button states, including labels, classes and `aria-pressed`.
- The suite is green at every phase boundary.

### Development workflow (Lesson 10)

- **Phase 1** is implemented with the project's existing testing and feedback conventions: tests follow the Testing section above, the full suite and Ruff checks run, and the developer then verifies the phase manually in the browser. Phase 1 does not use the `/tdd` skill or its RED/GREEN pauses; the skill doesn't exist yet.
- **After Phase 1 is manually verified**, a `/tdd` skill is created and used for **Phase 2**. For that phase it:
  1. Selects **at most three** important, testable behaviors from Phase 2's acceptance criteria, then **pauses for the developer's approval**.
  2. For each approved behavior, writes **one test at a time** and runs it to confirm it fails on an assertion (**RED**), not on an import, syntax or setup error. Then it **pauses** again.
  3. Implements just enough code to pass that test (**GREEN**), runs the regression tests, then **pauses for the developer's review** before the next behavior.
- Every other Phase 2 requirement, and every later phase, is implemented and tested normally.
- Which behaviors are chosen for `/tdd` depends on how the plan splits the phases. They must be behaviors Phase 1 hasn't already built, or their tests would pass straight away and could never be RED. Behaviors such as cross-user privacy, newest-first ordering, and "viewing never creates a wishlist" are candidates only if they are new in Phase 2. The final choice is the developer's, when the skill proposes it.

## Out of Scope

Excluded in the original request:

- Multiple wishlists per user.
- Named wishlists.
- Shared or public wishlists.

Excluded by decisions in this PRD:

- A wishlist count badge in the navbar, and the context processor it would need (Q12).
- Removing items directly from the wishlist page; removal happens on the product detail page (Q10).
- Saving products that aren't for sale (Q5).
- A back-office screen for employees to browse wishlists, and any "most wishlisted" analytics (Q8).
- Showing wishlist hearts on catalog cards; the button appears only on the product detail page (Q9).
- Keeping a record of deleted products in wishlists; they disappear with the product (Q11).
- Special handling of HTMX requests after a session expires; this stays the same as add-to-cart (Q6).

Not discussed in the interview, and not part of this feature:

- "Back in stock" notifications.
- Moving items between the wishlist and the cart.

## Further Notes

- The wishlist deliberately mirrors the cart: one per user, created when first needed, a unique product pair, actions looked up through the owner, an HTMX partial that replaces itself, and Django-admin-only visibility for staff. Anyone who knows the cart code should recognize the wishlist code.
- Seeding already empties every wishlist in a database, because it deletes all products and wishlist items cascade with them. The explicit wipe also removes the leftover empty `Wishlist` rows.
- When implementation lands, `CLAUDE.md`'s project layout should list the `wishlist` app and point to this PRD and its plan. That edit is deferred until the developer asks for it.
- The `/tdd` skill doesn't exist yet. It's created only after Phase 1 is manually verified (see Development workflow).
