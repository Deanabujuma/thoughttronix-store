# Plan: The ThoughtTronix Store — Wishlist

> Source PRD: `prd/wishlist.md`

*The PRD owns the decisions; this plan owns the sequence. Each phase is a thin vertical slice through model, migration, view, template, and tests. The suite and Ruff are green at every phase boundary, and each phase ends with the developer's browser verification before the next begins.*

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning app**: a new `wishlist` app, namespace `wishlist`, with templates in `templates/wishlist/` and HTMX partials in `templates/wishlist/partials/`. No new service module: the project's three deliberate deep modules stay as they are. Logic lives in model methods; views stay thin.
- **URLs** (all named, under the `wishlist:` namespace):

  | Path | Name | Method | Sign-in |
  |---|---|---|---|
  | `/wishlist/` | `wishlist:list` | GET | required |
  | `/wishlist/save/<int:pk>/` | `wishlist:save` | POST only | required |
  | `/wishlist/remove/<int:pk>/` | `wishlist:remove` | POST only | required |

  In save and remove, `pk` is the **product's** pk, following add-to-cart's `orders:add`. It is never a `WishlistItem` pk.
- **Models**:
  - `Wishlist`: a one-to-one link to the user (`CASCADE`), created only through `Wishlist.for_user(user)`, mirroring `Cart.for_user`.
  - `WishlistItem`: a wishlist (`CASCADE`), a product (`CASCADE`) and `added_at`, with a unique wishlist–product constraint named in the cart's style. Default ordering is newest first.
  - Model methods: save (get-or-create), remove (harmless when absent), and a **read-only** "has this user saved this product?" check that never creates a wishlist.
  - Migration: one initial migration for the new app. No changes to existing models.
- **Auth and authorization**: every wishlist view uses `LoginRequiredMixin` and is open to every signed-in user (customers, staff, admin), matching the cart. Every lookup goes through `request.user`, so another user's wishlist is never read or changed. No back-office screen. The Django admin gets a `WishlistAdmin` with a `WishlistItem` inline, mirroring `CartAdmin`.
- **Availability**: save looks products up through `Product.objects.available()`, so an unavailable or unknown product returns 404. Remove looks products up among all products. Marking a product unavailable keeps it saved.
- **HTMX**: the button partial replaces itself (`hx-post`, `hx-swap="outerHTML"`). There's no out-of-band swap, no navbar count, and no wishlist context processor. The CSRF header already comes from `base.html`.
- **Detail page state**: `ProductDetailView` passes a `saved` boolean from the read-only check, the same way the add-to-cart partial receives `in_cart`.
- **Templates**: Tailwind and DaisyUI only, with no JavaScript beyond HTMX.
- **Tests**: pytest and pytest-django, with shared plain fixtures in the project-level `conftest.py` per `docs/TESTING.md`. Topic files: `wishlist/test_models.py`, `wishlist/test_views.py`, `wishlist/test_privacy.py`, `wishlist/test_list_page.py`, plus additions to the existing product-detail and seed tests.
- **Data safety**: `seed` is never run against the developer's `db.sqlite3` during implementation. It is exercised only through the test suite's isolated database. `db.sqlite3` is never modified, reset, deleted, or committed.

## Development workflow (Lesson 10)

- **Phase 1** is built with the project's existing testing and feedback conventions: tests per `docs/TESTING.md`, then the full suite and Ruff, then the developer's browser verification. Phase 1 does **not** use `/tdd`.
- **After Phase 1 is verified in the browser**, the `/tdd` skill is created. It is used in **Phase 2** only:
  1. It selects **at most three** important, testable behaviors from Phase 2's acceptance criteria and **pauses for approval**.
  2. For each approved behavior, it writes **one test**, runs it, and confirms it fails on an **assertion** (RED), not on an import, syntax, URL, or setup error. Then it **pauses**.
  3. It implements just enough code to pass (GREEN), runs the regression tests, and **pauses for review** before the next behavior.
- Every other requirement in Phase 2, and all of Phase 3, is implemented and tested normally.

## Phase boundaries

A phase is complete only when:

- [ ] all of its acceptance criteria are met
- [ ] `uv run pytest` passes in full
- [ ] `uv run ruff check .` and `uv run ruff format --check .` are clean
- [ ] the developer has completed its browser verification

Nothing is committed until the developer asks. The next phase starts only after the developer approves the current one.

---

## Phase 1: Save and remove from the product page

**User stories**: 1, 2, 3 (actions), 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 21 (actions), 22, 23, 24, 25, 26, 29 (detail page)

### What to build

The tracer bullet. It creates the `wishlist` app with `Wishlist` and `WishlistItem` and their migration, the model methods, and the `save` and `remove` endpoints with their shared base view. It adds the button partial in all four states and wires it into the product detail page beside add-to-cart, with `ProductDetailView` supplying `saved`. It also registers `WishlistAdmin`.

A signed-in shopper can save and remove any available product without a reload, and the button always reflects the database. A product that becomes unavailable stays saved and can still be removed, while an unavailable product that isn't saved shows a disabled button. Signed-out visitors get a sign-in link that returns them to the product. There is no wishlist list page yet.

### Acceptance criteria

**Models and migration**
- [ ] The `wishlist` app is installed and its URLs are mounted under the `wishlist` namespace. The initial migration creates `Wishlist` and `WishlistItem`.
- [ ] `Wishlist` is one per user, and `Wishlist.for_user()` creates it on first call and returns the same one afterwards.
- [ ] The database rejects a second `WishlistItem` for the same wishlist and product.
- [ ] Saving a product twice keeps exactly one item. Removing a product that isn't saved does nothing and raises no error.
- [ ] The read-only check returns `False` for a user with no wishlist and creates no `Wishlist` row. It returns `True` only for the user who saved the product.
- [ ] Deleting a product removes its wishlist items. Deleting a user removes their wishlist and its items. Marking a product unavailable leaves it saved.

**Endpoints**
- [ ] `wishlist:save` and `wishlist:remove` accept POST only; GET is refused with 405.
- [ ] Signed-out POSTs redirect to login and change nothing.
- [ ] Save creates the wishlist when needed (through `for_user`) and returns the button partial, not a full page, in the **saved** state.
- [ ] Remove returns the button partial in the **not saved** state (or the **disabled** state for an unavailable product), and never creates a wishlist.
- [ ] Saving an unavailable or unknown product returns 404 and saves nothing.
- [ ] Removing a saved product that has since become unavailable succeeds.
- [ ] Customers, staff, and admin can all save and remove.

**Privacy**
- [ ] Saving or removing as user A never creates, changes, or deletes anything in user B's wishlist, including when both have saved the same product.
- [ ] The detail page's `saved` state is per user: B sees "not saved" for a product only A saved.

**Detail page and button**
- [ ] The button sits next to the add-to-cart control on the product detail page.
- [ ] Signed out: a button-styled "♡ Save to wishlist" link to `accounts:login` with `next` set to the current product page.
- [ ] Available, not saved: "♡ Save to wishlist", an outlined secondary button posting to `wishlist:save`, with `aria-pressed="false"`.
- [ ] Saved (available or unavailable): "♥ Saved — remove", a filled secondary button posting to `wishlist:remove`, with `aria-pressed="true"`.
- [ ] Unavailable, not saved: a disabled, outlined "♡ Save to wishlist" that does not post, so there's only one "Unavailable" label on the page.
- [ ] Every interactive button uses `hx-swap="outerHTML"` and updates only itself.
- [ ] Opening the detail page, signed in or out, never creates a `Wishlist` row.

**Admin and back office**
- [ ] The Django admin lists wishlists by user, with items inline and search by username.
- [ ] The back office has no wishlist screen.

### Testing

- `wishlist/test_models.py`: `for_user`, the unique constraint, idempotent save and remove, the read-only check, cascades, and unavailable products staying saved.
- `wishlist/test_views.py`: POST-only, sign-in required, partial responses and their states, the save 404, removing an unavailable product, and staff and admin access.
- `wishlist/test_privacy.py`: the action and detail-page privacy cases above.
- Product detail tests: all four button states (labels, classes, `aria-pressed`, target URL, disabled), and no wishlist created by viewing.
- Shared fixtures (a second customer, an unavailable product, a saved item) go in `conftest.py`.

### Browser verification

Use your existing accounts; don't run `seed`. To make a product unavailable, sign in as staff and use **Back office → Products → Edit**, untick **Available**, then tick it again afterwards.

1. Signed out, open any product. You should see a "♡ Save to wishlist" button. Click it. You should reach the login page, and after signing in you should land back on the same product.
2. Click **Save**. The button should change to "♥ Saved — remove" without a page reload; the URL and scroll position stay the same.
3. Reload the page. It should still show "Saved".
4. Click **Saved — remove**. It should change back to "♡ Save to wishlist" without a reload.
5. Double-click **Save** quickly. In step 9, confirm the product appears only once.
6. In an InPrivate window, sign in as a different user and open the same product. It should show **not saved**.
7. Save a product, then mark it unavailable as staff. As the shopper, reload it. It should still show "♥ Saved — remove", and clicking it should remove it.
8. With the product still unavailable and not saved, reload. You should see a **disabled** "♡ Save to wishlist" next to add-to-cart's "Unavailable", with only one "Unavailable" label. Make the product available again.
9. As the admin, open `/admin/` → **Wishlists**. Each user's items should appear inline, and the product from step 5 should appear only once.
10. As staff, confirm the back office has no wishlist screen.

---

## Phase 2: My Wishlist page

**User stories**: 3 (list), 16, 17, 18, 19, 20, 21 (list), 29 (list page)

### What to build

A read-only page at `/wishlist/` (`wishlist:list`), linked from the navbar for signed-in users. It lists only the signed-in user's saved products, newest first, each with image, name, price, availability, and a link to the product's detail page, and shows a designed empty state when there's nothing to show. Viewing the page never creates a wishlist. Removing still happens on the detail page.

**Order of work:** first, built **normally**, a minimal skeleton: the route, a `LoginRequiredMixin` view, and a page shell extending `base.html`. That way a `/tdd` test fails on an assertion rather than on a missing URL. Then the `/tdd` skill drives the behaviors you approve. Everything else is built normally.

### Acceptance criteria

- [ ] `wishlist:list` at `/wishlist/` requires sign-in; signed-out visitors are redirected to login.
- [ ] The page shows **only** the signed-in user's saved products, never another user's.
- [ ] Items are listed newest first by `added_at`, even when that differs from the order the rows were created.
- [ ] Each item shows the product's image, name, price, and availability, and links to its detail page.
- [ ] Products are loaded efficiently (no query per item).
- [ ] A designed empty state appears for a user with no wishlist and for a user with an empty wishlist.
- [ ] Viewing the page never creates a `Wishlist` row.
- [ ] The navbar shows a plain "Wishlist" link for signed-in users only, with no count badge.
- [ ] The page uses only Tailwind and DaisyUI classes, with no JavaScript.

### `/tdd` candidates (approved as a starting point)

The `/tdd` skill makes the final selection of **at most three** behaviors and pauses for approval. Candidates:

1. **Privacy:** user A's page shows A's saved product and not user B's. This is RED against the skeleton because A's item is missing.
2. **Newest first:** items with `added_at` times that **don't** match their creation order appear newest first. This is RED until ordering by `added_at` exists.
3. **Empty state without creating a wishlist:** a user with no wishlist sees the empty state, and no `Wishlist` row is created. This is RED because the skeleton has no empty-state message.

These can't genuinely fail first, so they are tested normally: "viewing creates no wishlist" on its own (the skeleton already passes it), the row details, the navbar link, and the query count.

### Testing

- `wishlist/test_list_page.py`: sign-in redirect, ordering, row contents and link, both empty states, no wishlist created, navbar link shown only when signed in, query efficiency.
- `wishlist/test_privacy.py`: the list-page privacy case is added.
- `/tdd` tests are written one at a time with the pauses above. All other tests are written normally.

### Browser verification

1. As a user who has never saved anything, click **Wishlist** in the navbar. You should see the designed empty state, not a blank page.
2. Save three products, one after another. Open **Wishlist**. The **last one saved** should be at the top, and each item should show its image, name, price, and availability.
3. Click a product's name. It should open that product's detail page.
4. Remove one product on its detail page, then return to **Wishlist**. It should no longer be listed.
5. Save a product, mark it unavailable as staff, and open **Wishlist**. It should still be listed and marked unavailable. Make it available again.
6. In an InPrivate window, sign in as another user and open `/wishlist/`. Only that user's products should appear.
7. Sign out. The navbar should have no Wishlist link, and opening `/wishlist/` directly should redirect to login.

---

## Phase 3: Demo wishlist in seed

**User stories**: 27, 28

### What to build

The demo world gets a wishlist. A `CUSTOMER_WISHLIST` constant, mirroring `CUSTOMER_CART`, names two or three available products and one unavailable product for the demo `customer` login. A `_create_customer_wishlist()` step builds it with fixed `added_at` times so the newest-first order never changes. `_wipe()` explicitly deletes all wishlists beside the carts. The seed's success message and the README mention the wishlist.

### Acceptance criteria

- [ ] After seeding, `customer` has a wishlist containing exactly the `CUSTOMER_WISHLIST` products, including one unavailable product.
- [ ] The items' `added_at` values are fixed, so `/wishlist/` shows the same order on every run.
- [ ] `_wipe()` deletes all `Wishlist` rows. No other seeded user has a wishlist, and no empty wishlists remain.
- [ ] Running `seed` twice gives an identical wishlist (same products, same order).
- [ ] The seed's success message mentions the demo wishlist.
- [ ] The README's description of the demo world mentions the wishlist.
- [ ] `seed` still sends no email.

### Testing

- The existing seed tests are extended: the demo wishlist's contents and fixed order, the unavailable item, the wipe, and repeatability.
- These run **only** in the test suite's isolated database. Implementation never runs `seed` against `db.sqlite3`.

### Browser verification

Running `seed` replaces the demo world and empties **every** wishlist in that database, including your test accounts' wishlists. Choose one:

- **Automated only:** rely on the seed tests above, or
- **Against a copy:** first copy `db.sqlite3` somewhere safe yourself, run `uv run python manage.py seed`, sign in as `customer` / `customer123`, open **Wishlist**, and check the seeded items in their fixed order, with one marked unavailable. Open that item and check that it shows "♥ Saved — remove". Then restore your copy.

---

## Story coverage

| Phase | Stories |
|---|---|
| 1 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 21, 22, 23, 24, 25, 26, 29 |
| 2 | 3, 16, 17, 18, 19, 20, 21, 29 |
| 3 | 27, 28 |

All 29 stories are covered. Story 3 (no visitor access) and story 21 (only the owner can see or change a wishlist) apply to the actions in Phase 1 and the list page in Phase 2. Story 29 (browsing never creates a wishlist) applies to the detail page in Phase 1 and the list page in Phase 2.

## Not in any phase

- The `CLAUDE.md` update: listing the `wishlist` app in the project layout and pointing to `prd/wishlist.md` and this plan. It waits until the developer asks for it.
- Creating the `/tdd` skill itself, which happens between Phase 1's browser verification and the start of Phase 2.
