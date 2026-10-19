# Plan: The ThoughtTronix Store — Product Reviews

> Source PRD: `prd/product-reviews.md`

*The PRD owns the decisions; this plan owns the sequence. Each phase is a thin vertical slice through model, migration, view, template, and tests. The suite and Ruff are green at every phase boundary, and each phase ends with the developer's browser verification (or, for Phase 6, the approved automated verification) before the next begins. Approved by the developer on 2026-10-18 as six phases, with Phases 4 and 5 kept separate. Phase 7 was added later the same day as a correction: inline HTMX for create, edit and delete (PRD, **Amendment: inline HTMX review actions**).*

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning app**: a new `reviews` app, namespace `reviews:`, with templates in `templates/reviews/` following `docs/TEMPLATES.md`. No new deep module: the project's three deliberate deep modules stay as they are. Rules live in a `ReviewQuerySet`/manager and model methods; views stay thin.
- **Customer URLs** (built from the product slug and `request.user`; no review pk ever appears):

  | Path | Name | Methods |
  |---|---|---|
  | `/products/<slug>/review/` | `reviews:create` | GET, POST |
  | `/products/<slug>/review/edit/` | `reviews:edit` | GET, POST |
  | `/products/<slug>/review/delete/` | `reviews:delete` | GET (confirmation), POST |

  Phase 7 adds HTMX responses on these same URLs. It adds no new URLs.

- **Back-office URLs** use the existing `/backoffice/` prefix and `StaffRequiredMixin` (`accounts/mixins.py`), with `section = "reviews"`. The tab goes between Discount codes and Dashboard in `templates/backoffice/base.html`:

  | Path | Name | Methods |
  |---|---|---|
  | `/backoffice/reviews/` | `reviews:manage_reviews` | GET |
  | `/backoffice/reviews/<pk>/` | `reviews:manage_review_detail` | GET |
  | `/backoffice/reviews/<pk>/hide/` | `reviews:manage_review_hide` | POST only |
  | `/backoffice/reviews/<pk>/restore/` | `reviews:manage_review_restore` | POST only |
  | `/backoffice/reviews/restrictions/` | `reviews:manage_restrictions` | GET |
  | `/backoffice/reviews/restrictions/<pk>/clear/` | `reviews:manage_restriction_clear` | GET (confirmation), POST (removal) |

- **Models**:
  - `Review` is created **complete in Phase 1**, with every PRD field: `status` (default `PUBLISHED`), `hidden_by`, `hidden_at`, `hidden_reason`, `created_at` (`default=timezone.now`) and `edited_at`. It has all three constraints: the unique pair, the rating check, and the hidden-state check. Later phases add behavior, not columns, so moderation needs no further `Review` migration.
  - `Review.objects.published()` is the **single published-only filter** from Phase 1. Every public list, average, count and catalog annotation goes through it, so hidden reviews drop out everywhere once Phase 4 can hide them.
  - `ReviewRestriction` arrives in Phase 5, as the app's second migration.
  - **No changes to existing tables.** `Product`, `Order`, `OrderItem` and `User` get no new columns. `ProductQuerySet.with_ratings()` (Phase 3) is a queryset method only and needs no migration.
- **Authorization**: one central set of rules (`can_create`, `can_edit`, `can_delete`, and a visitor-state helper), called by both templates and views, checked on GET and POST. Anonymous → login with `next`. Signed in but not allowed → 403. Unknown slug → 404. Edit or delete with no review → 404.
- **Templates**: Tailwind and DaisyUI only. Stars use DaisyUI `rating` radio inputs with no JavaScript. Comments and reasons are auto-escaped, never `|safe`.
- **Tests**: pytest and pytest-django per `docs/TESTING.md`, with shared plain fixtures in `conftest.py`. Topic files: `reviews/test_models.py`, `test_eligibility.py`, `test_views.py`, `test_display.py`, `test_pagination.py`, `test_catalog.py`, `test_backoffice.py`, `test_restrictions.py`, `test_admin.py`, plus additions to the existing seed and product-delete tests.
- **Data safety**:
  - `seed` is never run against the developer's `db.sqlite3`. It is exercised only through the test suite's isolated database.
  - `db.sqlite3.before-wishlist-backup` is **never** modified, moved, overwritten or deleted.
  - **Before the first local `migrate`** (needed for Phase 1's browser verification), work stops. Claude helps the developer create `db.sqlite3.before-reviews-backup`, and only with the developer's go-ahead. The command copies to a new file and refuses to overwrite an existing one. Only after the developer confirms the backup is `migrate` run.
  - `db.sqlite3` is never reset, deleted or committed.

## Development workflow (Lesson 10)

- Each phase runs through `/implement`, which delegates to `/tdd`. Every checkpoint is kept:
  1. `/tdd` proposes **at most three** behaviors from the phase's candidates below and **pauses for approval**.
  2. For each approved behavior, it writes one test and confirms it fails on an **assertion** (RED), not on an import, syntax, URL or setup error. Then it **pauses**.
  3. It implements just enough to pass (GREEN), runs the regression tests, and **pauses for review**.
  4. The rest of the phase is implemented and tested normally, followed by the browser verification.
- A minimal skeleton (route, view shell, model stub) is built normally first, so that RED fails on an assertion.
- The candidates listed per phase are proposals. The developer's selection at `/tdd`'s checkpoint is final.

## Phase boundaries

A phase is complete only when:

- [ ] all of its acceptance criteria are met
- [ ] `uv run pytest` passes in full
- [ ] `uv run ruff check .` and `uv run ruff format --check .` are clean
- [ ] the developer has completed its browser verification (Phase 6: the approved automated verification)

Nothing is committed until the developer asks. The next phase starts only after the developer approves the current one.

---

## Phase 1: Write a review and see it on the product page

**User stories**: 1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 20, 21, 26

### What to build

The tracer bullet. It creates the `reviews` app and the complete `Review` model with its migration, the `published()` queryset, `can_create`, and the visitor-state helper. It adds `ReviewForm` and the create view, and the product detail page's rating summary, a published "Verified buyer" list (unpaginated for now), and a basic "Your review" area. It also registers `ReviewAdmin`.

An eligible customer can submit a review and see it immediately. Everyone else sees the right message or nothing.

### Acceptance criteria

**Model and migration**
- [ ] The `reviews` app is installed and its URLs are mounted under `reviews:`. The initial migration creates **only** the `reviews_review` table.
- [ ] `Review` has every PRD field, including `status` (default published) and the moderation fields, with `created_at` defaulting to now and `edited_at` nullable.
- [ ] The database rejects a second review for the same user and product (`unique_review_user_product`), a rating outside 1–5, and a status/moderation mismatch (hidden ⇔ `hidden_at` set and reason non-empty).
- [ ] Comments are trimmed, and a whitespace-only comment is stored as `""`.
- [ ] `Review.objects.published()` returns only published reviews. A review created with hidden status directly in a test is excluded.
- [ ] Ordering is `-created_at`, `-pk`.
- [ ] No existing table gains or loses a column (checked by `makemigrations --check` showing only the new app).

**Eligibility**
- [ ] `can_create` is true only for a regular customer with a Delivered order containing **this product record** (by FK), and no existing review.
- [ ] Placed, Shipped and Cancelled orders, staff, superusers and anonymous users never qualify. Unavailable products still can.

**Create flow**
- [ ] Anonymous GET or POST → login with `next`. Signed in but ineligible → 403 on GET and POST. Unknown slug → 404.
- [ ] `ReviewForm` requires a 1–5 rating and allows an optional comment of at most 2,000 characters. Errors re-display on the form page.
- [ ] Stars are a fieldset with the legend "Your rating" and five labeled radios ("1 star" … "5 stars"), and work without JavaScript.
- [ ] Success redirects to `product_url#reviews` with a flash message.
- [ ] A duplicate submit is caught in a savepoint and redirects with "You've already reviewed this product." It never gives a 500 or a second row.

**Product detail page**
- [ ] The summary near the price shows the published-only average (one decimal), half-rounded stars (`aria-hidden`), and the count, with the label "Rated 4.3 out of 5, 12 reviews". It shows "No reviews yet" when the count is zero.
- [ ] The `#reviews` section lists published reviews as "Verified buyer," with stars, the escaped comment (`linebreaksbr`) and "Posted <date>". No username, email or name appears.
- [ ] The visitor's own review is pinned as "Your review" and excluded from the list below it.
- [ ] The "Your review" area shows the anonymous, ineligible, eligible and staff rows of the PRD table.
- [ ] The empty state reads "No reviews yet. Customers who've received this product can share their thoughts."

**Admin**
- [ ] `ReviewAdmin` lists user, product, rating, status and dates, searches by username and product name, and filters by status. `status`, `hidden_by`, `hidden_at` and `hidden_reason` are read-only.

### `/tdd` candidates

1. Only a Delivered order of the exact product FK qualifies; Placed, Shipped, Cancelled and staff are refused.
2. A double submit creates exactly one row and never a 500.
3. The average and count include published reviews only.

### Testing

- `reviews/test_models.py`: the constraints, trimming, `published()`, and ordering.
- `reviews/test_eligibility.py`: the eligibility matrix.
- `reviews/test_views.py`: create GET/POST responses, form errors, and the duplicate submit.
- `reviews/test_display.py`: the summary, aria label, "Verified buyer" with no username, escaping of a `<script>` comment, and the Phase 1 "Your review" rows.
- `reviews/test_admin.py`: read-only moderation fields.
- Shared fixtures (a customer with a Delivered order, a review, a staff user) go in `conftest.py`.

### Browser verification

**Stop first:** before `migrate`, Claude helps the developer create `db.sqlite3.before-reviews-backup` (new file only, never overwriting, never touching `db.sqlite3.before-wishlist-backup`). `migrate` runs only after the developer confirms. `seed` is not run.

1. Signed out, open a product. You should see "No reviews yet" and "Sign in to review". After signing in, you return to the product.
2. As a customer with a Delivered order for it, click **Write a review**. Tab through the stars with the keyboard and submit 4 stars with a comment. You land on `#reviews` with a message, and the review is pinned as "Your review".
3. Submit the form again from a second tab. You should get "You've already reviewed this product," with no error page.
4. As a customer whose order is only Placed or Shipped, see the ineligible message. Visiting `/products/<slug>/review/` directly gives 403.
5. As staff, see no **Write a review** button. The direct URL gives 403.
6. In an InPrivate window, view the page source and confirm no username appears.
7. In `/admin/`, open the review and confirm the moderation fields are read-only.

---

## Phase 2: Edit and delete your own review

**User stories**: 13, 14, 15, 16, 17, 18, 19, 27

### What to build

`can_edit` and `can_delete`, the edit view, the delete view with a GET confirmation, and `Review.delete_by_author()` for published reviews. The restriction branch for hidden reviews is added in Phase 5. "Edited <date>" appears, along with the "Delete only" rows for authors who became staff or are no longer eligible.

### Acceptance criteria

- [ ] `can_edit` requires the author, current eligibility and published status. `can_delete` requires only the author.
- [ ] Edit and delete pages: anonymous → login, no review of yours → **404**, signed in but not allowed to edit → 403.
- [ ] Edit sets `edited_at` **only** when the rating or comment actually changes. It never changes `created_at` or the review's position.
- [ ] "Edited <date>" appears on changed reviews, both pinned and public.
- [ ] Delete shows a confirmation on GET (which changes nothing). POST deletes through `delete_by_author()` and redirects to `#reviews` with a message.
- [ ] After deleting a published review, an eligible customer can write a fresh one.
- [ ] An author promoted to staff, or whose order is no longer Delivered, sees "Your review" with **Delete** only. Their published review stays published.
- [ ] Order status changes never alter an existing review.

### `/tdd` candidates

1. `edited_at` changes only on a real change, and `created_at` never changes.
2. An author promoted to staff can delete but not edit.
3. Edit and delete return 404 when the signed-in user has no review.

### Testing

- `reviews/test_views.py`: edit and delete GET/POST in each state, plus `edited_at`.
- `reviews/test_eligibility.py`: `can_edit` and `can_delete`, promotion to staff, and order status changes.
- `reviews/test_display.py`: "Edited <date>" and the Delete-only rows.

### Browser verification

1. Edit your review without changing anything and save. No "Edited" label appears.
2. Change the rating. "Edited <date>" appears, and the review keeps its place.
3. Delete it, confirm, and see **Write a review** again. Write a new one.
4. Visit `/products/<other-slug>/review/edit/` for a product you haven't reviewed. You should get 404.

---

## Phase 3: Pagination and catalog ratings

**User stories**: 2, 4 (catalog), AC 11, AC 12

### What to build

Review pagination on the detail page, and `ProductQuerySet.with_ratings()` with a shared summary partial on catalog and category cards.

### Acceptance criteria

- [ ] Ten published reviews per page through `?reviews=N`, newest `created_at` first, then `-pk`, with Newer/Older links to `#reviews` and no JavaScript.
- [ ] A non-numeric page shows page 1, and an out-of-range page shows the last page. Neither is ever a 404.
- [ ] The pinned own review appears once and is never counted in a page.
- [ ] `with_ratings()` annotates the published-only average and count. `CatalogView` and `CategoryView` use it.
- [ ] Cards show stars, average and count, or "No reviews yet". Unavailable products show ratings too.
- [ ] Counts are correct under search, tag and category filters, and the number of queries doesn't grow with the number of products.

### `/tdd` candidates

1. With 11 eligible reviewers, page 2 holds exactly the oldest review, and the order is newest first.
2. Invalid or out-of-range page numbers never 404.
3. Catalog annotation counts stay correct when filters are combined.

### Testing

- `reviews/test_pagination.py`: uses an isolated fixture that creates **at least 11** regular customers, each with their own Delivered order for the same product and one published review. Never uses seed data or the development database.
- `reviews/test_catalog.py`: annotation correctness, hidden reviews excluded (created directly in the test), and a query count with filters.

### Browser verification

Local data can't reach 11 reviews of one product without seeding, so pagination is proven by the tests above.

1. Open the catalog. Reviewed products show stars and a count, and the rest show "No reviews yet".
2. Filter by a tag and search. The ratings still show.
3. Visit a product with `?reviews=abc` and `?reviews=99`. Both show reviews, with no error.

---

## Phase 4: Back office — the Reviews tab with hide and restore

**User stories**: 22, 23, 28, 29, 30, 31, 32, 33, 34; AC 7, AC 8

### What to build

The Reviews tab, the list with filters, the detail page, `HideReviewForm`, and `Review.hide()` and `Review.restore()`, with POST-only endpoints. The author sees the hidden state on the product page.

### Acceptance criteria

- [ ] A "Reviews" tab appears between Discount codes and Dashboard. Every view uses `StaffRequiredMixin` (anonymous → login, non-staff → 403).
- [ ] The list shows 25 per page, newest first, with `?status=` All / Published / Hidden. Its columns are the linked product, username, stars, an excerpt of about 80 characters, the posted date, the status, and "Hidden by <username / Former staff member> on <date>".
- [ ] The detail page shows the full escaped comment, username, product, posted and edited dates, moderation details, and the Hide form or the Restore button.
- [ ] Hide requires a trimmed reason of 1–200 characters. An invalid reason re-displays on the detail page. `hide(by, reason)` sets the status, `hidden_by`, `hidden_at` and the reason.
- [ ] `restore()` sets the status back to published and clears the moderation fields.
- [ ] Hide and restore are POST-only and CSRF-protected, and redirect with a flash message. Repeating either shows an info message and changes nothing; the original reason is kept.
- [ ] A hidden review disappears from the public list, averages and catalog counts. Its author sees "Hidden by staff: <reason>" with **Delete** only.
- [ ] Deleting the moderator's account leaves the review hidden and shows "Former staff member".
- [ ] There's no back-office delete. Empty states are designed for an empty list and an empty filter result.

### `/tdd` candidates

1. Hiding an already-hidden review keeps the original reason.
2. Hide and restore refuse GET and non-staff users.
3. A hidden review leaves the public list and averages but stays visible to its author.

### Testing

- `reviews/test_backoffice.py`: access, filters, POST-only, reason validation, idempotency, "Former staff member", and no delete action.
- `reviews/test_display.py`: the hidden author row, and hidden reviews excluded from public output.

### Browser verification

1. As staff, open **Back office → Reviews**. Filter by Published and by Hidden.
2. Try hiding a review with an empty reason. You should see an error. Hide it with a reason.
3. As the author, see "Hidden by staff" with Delete only. As a visitor, the review is gone and the count dropped.
4. Restore it. It comes back for everyone.
5. As a customer, visit `/backoffice/reviews/`. You should get 403.

---

## Phase 5: Restrictions

**User stories**: 24, 25, 35, 36, 37; AC 5, 6, 9, 14, 15, 16

### What to build

The `ReviewRestriction` model and migration, the hidden-review branch of `delete_by_author()`, restriction-aware `can_create`, the Restrictions page with a two-step Clear, `ReviewRestrictionAdmin`, and the product-delete review warning.

### Acceptance criteria

- [ ] The app's second migration creates only `reviews_reviewrestriction`, with `unique_restriction_user_product`.
- [ ] Deleting a **hidden** review creates a restriction in the same transaction, copying the reason, `hidden_by` and `hidden_at`, and never the rating or comment. An existing restriction is **updated, not duplicated**. Deleting a published review creates none.
- [ ] A restricted customer sees "You cannot currently review this product. If you believe this is a mistake, please contact our team." Create is refused on GET and POST, and their other eligible products are unaffected.
- [ ] The Restrictions page lists active restrictions, 25 per page. Columns are username, product, reason, hidden by (or "Former staff member"), hidden at, and restricted at. A designed empty state appears when there are none.
- [ ] Clear restriction: a GET shows a confirmation page naming the customer and product and changes nothing. Only a staff, CSRF-protected POST calls `clear()` and redirects with a message. An already-cleared restriction redirects with an info message.
- [ ] `ReviewRestrictionAdmin` is registered with read-only audit fields. Admin deletion of a hidden review creates no restriction.
- [ ] `ManageProductDeleteView` warns "This will also permanently delete N reviews. This can't be undone in the store." when N > 0.
- [ ] Deleting a product or customer cascades to reviews and restrictions. Deleting a moderator sets `hidden_by` to NULL and leaves restrictions active.

### `/tdd` candidates

1. Deleting a hidden review creates the restriction atomically and keeps no rating or comment.
2. An existing restriction is updated rather than duplicated.
3. A GET to clear changes nothing; only a staff POST clears.

### Testing

- `reviews/test_restrictions.py`: `delete_by_author` branches, the restriction message, other products unaffected, the Clear GET/POST, and idempotency.
- `reviews/test_models.py`: cascades and SET_NULL.
- `reviews/test_admin.py`: admin deletion creates no restriction.
- `products/test_backoffice.py`: the delete warning count.

### Browser verification

1. As staff, hide a customer's review. As that customer, delete it. The restriction message appears in place of the form.
2. Confirm the customer can still review another eligible product.
3. As staff, open **Reviews → Restrictions**, then click **Clear restriction**. A confirmation page appears, and nothing changes until you confirm.
4. Confirm. As the customer, **Write a review** is back.
5. Open a reviewed product's delete page (don't confirm) and see the review-count warning.

---

## Phase 6: Seed

**User stories**: 38, 39, 40; AC 17

### What to build

Seed support for reviews, verified **only by automated tests on the isolated test database**, as the developer approved. `seed` is not run against `db.sqlite3`.

### Acceptance criteria

- [ ] `_wipe()` deletes `ReviewRestriction` rows, then `Review` rows.
- [ ] An independent fixed-seed review RNG runs after all existing draws. Seeded users, orders, coupons and dashboard figures are unchanged.
- [ ] The demo `customer`: MindSync published and edited; DreamWeaver hidden by `employee` with a reason; SyncRest unreviewed (shows **Write a review**); Seraphine Mini (Shipped) and Veil (Placed) show the ineligible message.
- [ ] Background reviews come only from customers' own Delivered orders. Ratings vary, some have comments and some don't, some products stay unreviewed, there are extra hidden reviews and at least one edited review, and there's exactly one background `ReviewRestriction`.
- [ ] Each review's `created_at` is its qualifying order's `created_at` plus a fixed offset, and `edited_at` and `hidden_at` are fixed offsets after it. All are timezone-aware UTC and earlier than the seed's `now`.
- [ ] No product has more reviews than distinct customers with a Delivered order for it (at most five with the current orders). No test asserts more than 10.
- [ ] The success message adds "N reviews (M hidden) and 1 review restriction."

### `/tdd` candidates

1. Every seeded review is eligible (a regular customer with a Delivered order for that product).
2. Timeline rules hold: review after order, edit and hide after review, nothing in the future.
3. Two runs at a frozen clock give identical review data, and existing order and dashboard seed tests pass unchanged.

### Testing

- Seed tests call the command against the pytest test database only: eligibility, demo states, timelines, frozen-clock determinism, the reviewer limit, and the unchanged order and dashboard figures.

### Automated verification (in place of browser verification)

1. `uv run pytest` passes in full, including the new and existing seed tests.
2. `uv run ruff check .` and `uv run ruff format --check .` are clean.
3. The developer reviews the seed test output. `db.sqlite3` and both backups are untouched.

---

## Phase 7: Inline HTMX for create, edit and delete (correction)

**Source**: PRD, **Amendment: inline HTMX review actions** (AC 19–23). This corrects interview Q13. The separate pages from Phases 1–2 stay as the no-JavaScript path.

### What to build

- **Product page:** the **Write a review**, **Edit** and **Delete** links keep their `href` and gain `hx-get`. The form or confirmation loads into `#your-review`, and submits with `hx-post` to the same URL.
- **Responses for HTMX requests:**
  - a success re-renders the `#reviews` section, plus `#rating-summary` out-of-band;
  - an invalid submit re-renders only the form;
  - a refusal keeps its status and tells HTMX to redirect or refresh.
- **Requests without HTMX** behave exactly as they do now.

### Acceptance criteria

- [ ] No new URLs, models, migrations or dependencies. The authorization rules and `OwnReviewMixin`'s order (login → 404 → 403) are unchanged.
- [ ] `hx-get` on create, edit and delete returns a partial (no `<html>`) that posts back to the same URL with a CSRF token. Edit is pre-filled. The delete GET changes nothing.
- [ ] A successful `hx-post` on create, edit or delete returns the `#reviews` section with `HX-Retarget: #reviews` and `HX-Reswap: outerHTML`, the flash message inside it, and an out-of-band `#rating-summary` with the new average and count.
- [ ] Invalid HTMX submissions return the form with its errors and change nothing. A duplicate HTMX create, repeated or concurrent, returns the section with "You've already reviewed this product.", leaves one row, and never returns a 500.
- [ ] HTMX refusals:
  - anonymous → 204 with `HX-Redirect` to the login page, with `next`;
  - not allowed → 403 with `HX-Refresh: true`;
  - no review of yours → 404 with `HX-Refresh: true`;
  - nothing changes in any case.
- [ ] `edited_at` changes only on a real change. Deleting runs through `delete_by_author()`, so a hidden review leaves a restriction and the section shows the restriction message.
- [ ] **Cancel** and **Keep it** restore the section (`hx-get` the product page with `hx-select="#reviews"`).
- [ ] Responses send `Vary: HX-Request`. HTMX responses escape comments and contain no username.
- [ ] An HTMX post without a CSRF token is refused (`enforce_csrf_checks`).
- [ ] The standalone pages contain no `hx-post`, and all 784 existing tests pass unchanged.
- [ ] The detail page and the HTMX success response build the section from one shared context helper.

### `/tdd` candidates

1. A successful HTMX create, edit or delete swaps the reviews section and the rating summary.
2. An invalid or duplicate HTMX submission re-renders only the form, or the section, and changes nothing.
3. Under HTMX, refusals keep their meaning: login with `next`, 403 and 404, with nothing changed.

### Testing

- `reviews/test_htmx.py`: everything above, with `headers={"HX-Request": "true"}`.
- The existing suite is the no-JavaScript regression check and is not edited.

### Browser verification

Use a temporary review, so the existing MindSync and DreamWeaver reviews stay as they are. Don't delete DreamWeaver, which would create a real restriction. No `migrate` or `seed` is needed.

1. **JavaScript on:**
   - **Write a review** opens inline, and the URL doesn't change.
   - Submitting with no stars shows the error inline.
   - A keyboard-chosen rating submits. The section, the summary near the price and the message all update.
2. **Edit:** an unchanged save shows no "Edited". A change shows "Edited", and the review keeps its place. **Cancel** restores the section.
3. **Delete:** the confirmation opens inline. **Keep it** restores the section. Confirming brings back **Write a review** and lowers the count.
4. **Double submit,** or a second tab, gives "already reviewed", with no error.
5. **DevTools → Network:** requests carry `HX-Request` and `X-CSRFToken`, and the responses are partials.
6. **Sign out in another tab, then click Edit:** you're sent to the login page.
7. **Staff** see no buttons, and the direct URLs give 403.
8. **JavaScript disabled:** all three flows work as full pages, as before.
9. **Refresh and Back** after inline actions show the true state.
