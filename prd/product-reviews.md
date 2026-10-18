# PRD: The ThoughtTronix Store — Product Reviews

*Settled in a design interview on 2026-10-16. Extends `prd/core-platform.md`; where the two disagree, this document wins for product reviews only.*

---

## Problem Statement

A ThoughtTronix shopper deciding whether to buy a product has only the store's own description to go on. There's no way to learn what people who actually received the product thought of it, and no way for a customer who has lived with a MindSync or a DreamWeaver to share that experience with the next buyer. The store has no ratings, so shoppers browsing the catalog can't compare products by how well they're liked either.

Any review system also brings risks the store must control: fake reviews from people who never bought the product, reviews from employees rating their own company's goods, abusive or private content, and customers deleting and reposting to get around moderation.

## Solution

Customers who have **received** a product (it was on a Delivered order) can leave **one** review of it: a required 1–5 star rating and an optional written comment. They can edit or delete it later from the product page.

Everyone, including signed-out visitors, can read published reviews. The product detail page shows the average rating, the number of reviews, and the review list (newest first, 10 per page). Catalog cards show each product's average and count. Public reviews are signed "Verified buyer," never with a username or name.

Reviews go live immediately. Staff moderate after the fact from a new **Reviews** tab in the back office. They can **hide** a review (with a required reason) and **restore** it later. A hidden review disappears from the public and stops counting. Its author still sees it with the reason and can delete it, but can't edit it. If an author deletes a hidden review, the store remembers a **restriction** that blocks them from reviewing that product again until staff clear it. That way, moderation can't be bypassed by deleting and reposting.

Employees and the admin can read reviews and moderate them, but can never write them.

## Goals

- Every published review is backed by a real, delivered purchase by a regular customer.
- Shoppers can judge products by honest ratings, on both the catalog and the detail page.
- Staff can take down inappropriate content quickly, reversibly, and with a recorded reason.
- Moderation cannot be bypassed by editing, deleting and reposting, or hand-crafted requests.
- No public page reveals any reviewer's account identity.
- Existing data, orders and dashboard figures are unchanged by this feature.

## User Stories

**Visitor (signed out)**

1. As a visitor, I want to read a product's published reviews and see its average rating, so that I can judge it before creating an account.
2. As a visitor, I want to see each catalog card's average rating and review count, so that I can compare products while browsing.
3. As a visitor, I want a "Sign in to review" link that returns me to the product after sign-in, so that I know how to leave a review.
4. As a visitor, I want products without reviews to say "No reviews yet" rather than "0.0 stars," so that a new product isn't shown as badly rated.

**Customer — eligibility**

5. As a customer with a Delivered order for a product, I want a "Write a review" button on its page, so that I can share my experience.
6. As a customer whose order for a product is only Placed or Shipped, I want to be told only customers who've received it can review it, so that I understand why I can't yet.
7. As a customer whose only order for a product was Cancelled, I want to be unable to review it, so that ratings reflect products people actually own.
8. As a customer, I want to review products that are no longer for sale if I received them, so that discontinued products still get honest feedback.
9. As a shopper, I want reviews to come only from verified recipients, so that I can trust the ratings.

**Customer — writing and managing a review**

10. As an eligible customer, I want to give a required 1–5 whole-star rating using accessible, labeled star buttons that work without JavaScript, so that rating is quick for everyone.
11. As an eligible customer, I want to add an optional comment of up to 2,000 characters, so that I can explain my rating if I choose.
12. As a customer, I want my review to appear immediately after I submit it, so that I see it worked.
13. As a customer, I want my own review pinned at the top of the reviews section as "Your review," so that I can find it.
14. As a customer, I want to edit my rating and comment while I remain eligible, so that I can fix mistakes or update my opinion.
15. As a shopper, I want to see "Edited <date>" on a changed review, so that I know it was revised.
16. As a customer, I want editing my review not to move it in the list, so that the order stays honest.
17. As a customer, I want to delete my own review after a confirmation step, so that I can withdraw my words.
18. As a customer, I want to always be able to delete my own review, even if my order status changed, it was hidden, or I became staff, so that I'm never stuck with words I want gone.
19. As a customer, I want to be able to write a fresh review after deleting a published one (if still eligible), so that I can start over.
20. As a customer, I want a double-click or second tab to never create a duplicate review or show an error page, so that submitting is safe.
21. As a customer, I want only one review per product, so that my opinion counts exactly once in the average.

**Customer — moderation as seen by the author**

22. As an author whose review was hidden, I want to see it marked "Hidden by staff" with the reason, so that I understand what happened.
23. As an author of a hidden review, I want to be unable to edit it, but able to delete it, so that moderation is respected and I keep control over my own words.
24. As a customer who deleted a hidden review, I want to see "You cannot currently review this product. If you believe this is a mistake, please contact our team." instead of the form, so that I know where I stand.
25. As a restricted customer, I want to still review my other eligible products, so that one restriction doesn't block me storewide.

**Employee and admin**

26. As an employee or admin, I want to read reviews like any shopper but never see a "Write a review" button, so that staff can't rate the company's own products.
27. As a customer later promoted to staff, I want my existing review to stay published, though I can no longer edit it or write new ones, so that history is kept without a conflict of interest.
28. As staff, I want a Reviews tab between Discount codes and Dashboard, listing reviews newest first with All / Published / Hidden filters, so that I can find what needs attention.
29. As staff, I want each review's detail page to show the full comment, author username, product and moderation history, so that I decide with full context.
30. As staff, I want to hide a review with a required reason of 1–200 characters, so that there's a clear record of why.
31. As staff, I want to restore a hidden review, so that a mistaken hide can be undone.
32. As staff, I want to see who hid a review and when, or "Former staff member" if their account was deleted, so that moderation is accountable.
33. As staff, I want repeated hide or restore clicks to change nothing, so that double-clicks are harmless.
34. As staff, I want no permanent delete button in the back office, so that moderation is never destructive.
35. As staff, I want a Restrictions page listing active restrictions with a confirmed "Clear restriction" action, so that a customer can be allowed to review again.
36. As staff, I want the product delete confirmation to warn how many reviews will be permanently deleted, so that I'm not surprised.
37. As the admin, I want reviews and restrictions in the Django admin, so that I can do direct data management, including permanent deletion.

**Developer**

38. As a developer, I want `seed` to build a repeatable demo world that shows every review state, so that the feature can be demonstrated immediately.
39. As a developer, I want every seeded review to satisfy the eligibility rules and a valid timeline, so that the demo never contradicts the feature.
40. As a developer, I want the existing seeded orders and dashboard figures unchanged, so that earlier features stay stable.

## Implementation Decisions

### A new `reviews` app

- A new Django app, namespace `reviews:`, with templates in `templates/reviews/`, following the template conventions.
- **No new deep module.** The three deliberate deep modules stay as they are. Rules live in model methods and managers, and views stay thin.

### Data model

**Review**

| Field | Definition |
|---|---|
| `user` | FK → user, **CASCADE**, `related_name="reviews"` |
| `product` | FK → `Product`, **CASCADE**, `related_name="reviews"` |
| `rating` | `PositiveSmallIntegerField`, validators 1–5 |
| `comment` | `TextField(max_length=2000, blank=True)`, trimmed; whitespace-only → `""` |
| `status` | `TextChoices`: `PUBLISHED` (default), `HIDDEN` |
| `hidden_by` | FK → user, **SET_NULL**, nullable |
| `hidden_at` | `DateTimeField`, nullable |
| `hidden_reason` | `CharField(max_length=200, blank=True)` |
| `created_at` | `DateTimeField(default=timezone.now)` (not `auto_now_add`, so the seed can set it) |
| `edited_at` | `DateTimeField`, nullable |

- Constraints:
  - `UniqueConstraint(user, product)`, named `unique_review_user_product`.
  - `CheckConstraint`: `rating` between 1 and 5.
  - `CheckConstraint`: hidden ⇔ `hidden_at` is set and `hidden_reason` is non-empty, so a hidden review always has its record and a published one never does. `hidden_by` is deliberately excluded, because it can become null.
- Ordering: `-created_at`, `-pk`.
- **Status is stored on its own** and never inferred from `hidden_by`.

**ReviewRestriction**

| Field | Definition |
|---|---|
| `user` | FK → user, **CASCADE** |
| `product` | FK → `Product`, **CASCADE** |
| `hidden_reason` | copied from the deleted review |
| `hidden_by` | FK → user, **SET_NULL**, nullable |
| `hidden_at` | copied from the deleted review |
| `created_at` | when the author deleted the hidden review |

- `UniqueConstraint(user, product)`, named `unique_restriction_user_product`.
- **Never stores the deleted review's rating or comment.**
- A row existing means the restriction is active. Clearing it deletes the row.

**No changes to existing tables.** `Product`, `Order`, `OrderItem` and `User` get no new columns. The only migrations are the new app's own.

### Eligibility and authorization (one central set of rules)

All rules live on the model, for example `Review.objects.can_create(user, product)`, `review.can_edit(user)` and `review.can_delete(user)`, plus a helper that reports the visitor's state for the template. Templates and views call the **same** functions. Views check them on **both GET and POST**.

- **Regular customer** = signed in, `is_staff=False`, `is_superuser=False`.
- **Qualifying purchase** = an `OrderItem` whose `product` **is this product record** (matched by FK, never by name or slug) on an `Order` owned by the user with status **Delivered**. Placed, Shipped and Cancelled never qualify.
- **Create** requires a regular customer, a qualifying purchase, no existing review of the product, and no restriction for (user, product). Product availability doesn't matter.
- **Edit** requires being the author, current eligibility (a regular customer with a qualifying purchase), and the review being published.
- **Delete** requires **being the author, and nothing else**. This holds even if the order status changed, the review is hidden, or the author became staff.
- **Existing reviews are never touched by order status changes.** A published review stays published if its order stops being Delivered.
- **"Verified buyer"** means the author qualified when they submitted. It isn't re-checked.
- **Responses:**
  - Anonymous → redirect to login with `next`.
  - Signed in but not authorized → **HTTP 403**.
  - Unknown product slug → 404.
  - Edit or delete page with no review of yours to act on → **404**.

### Customer flows and URLs (`reviews:` namespace)

Every URL is built from the product slug plus the signed-in user. No review pk appears anywhere, so no URL can reach another user's review.

| Name | URL | View |
|---|---|---|
| `reviews:create` | `/products/<slug>/review/` | `CreateView` |
| `reviews:edit` | `/products/<slug>/review/edit/` | `UpdateView` |
| `reviews:delete` | `/products/<slug>/review/delete/` | `DeleteView` (GET confirmation, POST deletes) |

- **Form:**
  - A `ReviewForm` owns the validation (rating required 1–5, comment ≤ 2,000 characters, trimmed).
  - Stars are a fieldset with the legend "Your rating" and five labeled radio inputs ("1 star" … "5 stars") styled with DaisyUI `rating`, with no JavaScript.
  - Errors re-display on the form page.
- **On success,** every action redirects to `product_url#reviews` with a flash message.
- **Edit** sets `edited_at` to now **only when the rating or comment actually changes**. Saving an unchanged form leaves it untouched. Editing never changes `created_at` or the review's position.
- **Delete runs through one model method, `Review.delete_by_author()`,** in a single `transaction.atomic()` block:
  - If the review is **hidden**, it creates the restriction (copying the reason, `hidden_by` and `hidden_at`) and then deletes the review. If a restriction already exists for the pair, it's **updated rather than duplicated**.
  - If the review is **published**, it just deletes it.
  - The customer delete view calls only this method.
  - A superuser deleting through the Django admin uses Django's ordinary delete and **never** creates a restriction.
- **Duplicate submissions:**
  - The create view saves inside a savepoint and catches the uniqueness `IntegrityError`.
  - It then redirects to the product with "You've already reviewed this product."
  - A double submit never produces a 500 error or a second row.

### Product detail page

- `ProductDetailView` adds:
  - the rating summary (the average of **published** reviews to one decimal place, and their count);
  - the visitor's review state;
  - the visitor's own review, if any;
  - a page of published reviews **excluding the visitor's own**.
- **Summary near the price:**
  - Shows "★★★★½ 4.3 · 12 reviews," with stars rounded to the nearest half.
  - Shows "No reviews yet" when the count is zero.
  - Screen-reader label: "Rated 4.3 out of 5, 12 reviews". The star icons are `aria-hidden`.
- **A `#reviews` section** below the product:
  - "Your review" (pinned, when present), then the public list.
  - Each public review shows "Verified buyer," its stars, the comment (escaped, `linebreaksbr`), "Posted <date>," and "Edited <date>" if set.
- **Pagination:**
  - 10 per page with Django's `Paginator`, using the `?reviews=N` parameter, with Newer/Older links to `#reviews`.
  - Order is newest `created_at` first, then `-pk`.
  - A non-numeric page shows page 1, and an out-of-range page shows the last page. Neither is ever a 404.
- **Hidden reviews never appear** in the public list, averages or counts.
- **Empty state:** "No reviews yet. Customers who've received this product can share their thoughts."

**The "Your review" area, by visitor:**

| Visitor | Shown |
|---|---|
| Anonymous | "Sign in to review" → login → back to product |
| Customer without a Delivered order | "Only customers who've received this product can review it." |
| Eligible customer, no review | **Write a review** button |
| Author, published review, still eligible | "Your review" + **Edit** / **Delete** |
| Author, hidden review | "Your review" + "Hidden by staff: <reason>" + **Delete** only |
| Author now staff or no longer eligible | "Your review" + **Delete** only |
| Restricted customer | "You cannot currently review this product. If you believe this is a mistake, please contact our team." |
| Staff / admin with no review | Nothing |

### Catalog cards

- A `ProductQuerySet.with_ratings()` annotation adds the published-only average and count. `CatalogView` and `CategoryView` use it.
- The counts stay correct when combined with search, tag and category filters, with no N+1 queries. A query-count test checks this.
- Cards show the same summary component as the detail page (stars, average, count, or "No reviews yet"). Unavailable products show ratings too.

### Back office — the Reviews tab

- **A "Reviews" tab** goes between Discount codes and Dashboard, with `section = "reviews"`.
- **URLs use the existing `/backoffice/` prefix**, matching `backoffice/products/` and the other tabs. No `/manage/` prefix is introduced.
- **All views use `StaffRequiredMixin`** (anonymous users go to login, signed-in non-staff get 403). Every state-changing request is **POST-only** and CSRF-protected, then redirects with a flash message.

| Name | URL | Methods | Purpose |
|---|---|---|---|
| `reviews:manage_reviews` | `/backoffice/reviews/` | GET | List, 25 per page, newest first, `?status=` All / Published / Hidden |
| `reviews:manage_review_detail` | `/backoffice/reviews/<pk>/` | GET | Full review, Hide form or Restore button, moderation details |
| `reviews:manage_review_hide` | `/backoffice/reviews/<pk>/hide/` | POST only | Hide with reason |
| `reviews:manage_review_restore` | `/backoffice/reviews/<pk>/restore/` | POST only | Restore |
| `reviews:manage_restrictions` | `/backoffice/reviews/restrictions/` | GET | Active restrictions, 25 per page |
| `reviews:manage_restriction_clear` | `/backoffice/reviews/restrictions/<pk>/clear/` | GET (confirmation page), POST (removal) | Clear a restriction |

- **List columns:**
  - product (linked to its public page), username, stars, comment shortened to about 80 characters, and posted date;
  - status, plus "Hidden by <username / Former staff member> on <date>" when hidden.
- **Detail page:** the full comment (escaped), the username, the product, the posted and edited dates, and the moderation details.
- **Hide:**
  - A `HideReviewForm` takes the reason, which is trimmed, required, and 1–200 characters. An invalid reason re-displays on the detail page.
  - `Review.hide(by, reason)` sets the status, `hidden_by`, `hidden_at = now` and the reason.
- **Restore:** `Review.restore()` sets the status back to published and clears `hidden_by`, `hidden_at` and `hidden_reason`.
- **Clear restriction is a two-step action:**
  - A **GET** shows a confirmation page naming the customer and product. GET never changes anything.
  - Only a **POST** (CSRF-protected, behind `StaffRequiredMixin`) removes the restriction, through `ReviewRestriction.clear()`. It then redirects to the Restrictions page with a flash message.
- **Idempotent:**
  - Hiding a hidden review, or restoring a published one, shows an info message and changes nothing. In particular, the original reason isn't overwritten.
  - Clearing an already-cleared restriction redirects with an info message.
- **No back-office delete** for reviews.
- **Restrictions list columns:** username, product, reason, hidden by (or "Former staff member"), hidden at, and restricted at.
- **Designed empty states** for an empty list, an empty filter result, and no restrictions. Tables follow the DaisyUI table convention.
- **Product delete confirmation** (`ManageProductDeleteView`): when the product has reviews, it says "This will also permanently delete N reviews. This can't be undone in the store."

### Django admin

- `Review` and `ReviewRestriction` are registered with:
  - a list display of user, product, rating or reason, status and dates;
  - search by username and product name;
  - filters by status.
- The moderation fields (`status`, `hidden_by`, `hidden_at`, `hidden_reason`) are **read-only** in the admin. Moderation goes through the back-office methods, so the audit fields stay consistent.
- The superuser can permanently delete reviews and restrictions. Admin deletion of a hidden review **does not** create a restriction.

### Account and product lifecycle

- **Customer account deleted:** their reviews and restrictions cascade away, and averages and counts update automatically, since nothing is cached.
- **Moderator account deleted:** `hidden_by` becomes NULL. Reviews stay hidden and restrictions stay active. The back office shows "Former staff member."
- **Product deleted:** its reviews and restrictions cascade away.
- **Product unavailable:** reviews still display and count, and eligible customers can still create and edit them.
- **Customer promoted to staff:** their review stays published, and they can delete it but not edit it or create new ones.

### Security

- **Server-side authorization:** every create, edit, delete and moderation request is checked on the server. Hiding a button is only presentation.
- **No IDOR:** customer URLs contain no review pk. Lookups always go through `request.user` and the product.
- **Moderation is staff-only** through `StaffRequiredMixin`. Every state change is POST-only and CSRF-protected. GET requests never change data.
- **Escaping:** comments and reasons are rendered with Django auto-escaping. Templates never apply `|safe`, and HTML and Markdown are never rendered.
- **Privacy:** no public page or response contains a reviewer's username, email or name.
- **Hidden reviews** are visible only to their author and staff.
- **Validation:** the rating range is enforced by the form, the model validators and the database constraint. The comment length is enforced by the form and the model.

### Seed

- **`_wipe()`** explicitly deletes `ReviewRestriction` and then `Review` rows.
- **The demo `customer`:**
  - **MindSync:** a published review, edited.
  - **DreamWeaver:** hidden by `employee` with a reason.
  - **SyncRest:** no review, so it shows **Write a review**.
  - **Seraphine Mini** (Shipped) and **Veil** (Placed) show the ineligible message.
- **Background customers:**
  - Reviews only for products on their own Delivered orders.
  - Varied ratings, some with comments and some without.
  - Some products with no reviews.
  - Extra hidden reviews, at least one edited review, and **one** `ReviewRestriction` on a background customer.
  - The seed does **not** aim for more than 10 reviews on one product. Reviews come only from customers with a qualifying Delivered order, and the existing seeded orders allow at most **five** eligible reviewers per product. The seeded detail pages therefore fit on one page. See Resolved Constraints.
- **Timestamps:**
  - Each review's `created_at` is its qualifying order's `created_at` plus a fixed offset, and `edited_at` and `hidden_at` are fixed offsets after the review.
  - All values are timezone-aware UTC, and every one is earlier than the seed's `now`.
  - Fixed calendar dates are deliberately **not** used, because the order timeline is relative to `now`.
- **Randomness** comes from an **independent fixed-seed RNG**. The order and coupon RNG sequences, seeded orders and dashboard figures stay exactly the same.
- **The success message** adds "N reviews (M hidden) and 1 review restriction."

### Testing

- Follows `docs/TESTING.md`: pytest and pytest-django, with shared plain fixtures in `conftest.py` (for example a delivered order for a customer, a review, a hidden review, a restriction, and a staff user).
- **Models:**
  - The constraints: unique pair, rating check, and hidden-state check.
  - Comment trimming.
  - `hide`, `restore` and `clear`, and their idempotency.
  - `delete_by_author`: a hidden review creates a restriction atomically and keeps no rating or comment; a published review creates none; an existing restriction is updated.
  - The cascades and SET_NULL.
  - Status staying independent of `hidden_by`.
- **Eligibility matrix:**
  - Delivered qualifies. Placed, Shipped and Cancelled don't.
  - Staff and superusers are refused.
  - Matching is by the product FK, not by name or slug.
  - Restricted customers are refused for that product only.
  - An existing review blocks a new one.
  - An order status change doesn't affect an existing review.
  - An author promoted to staff can delete but not edit.
- **Views:**
  - The GET and POST responses for each state: login redirect, 403, 404, and success redirect to `#reviews` with a message.
  - Form errors re-display.
  - A duplicate submit gives a graceful redirect with no second row.
  - `edited_at` is set only when something changes.
- **Display:**
  - Averages and counts are published-only, the one-decimal average, half-star rounding, and "No reviews yet."
  - The aria label.
  - "Verified buyer," with no username in the HTML.
  - The pinned own review isn't duplicated.
  - Pagination order, and invalid or out-of-range pages. Pagination is tested with isolated pytest fixtures, not seed data. The fixtures create **at least 11** regular customers, each with their own Delivered order for the same product and one published review of it, so that a second page exists. The development database is never used.
  - Escaping of a `<script>` comment.
  - Every row of the "Your review" table.
  - Catalog annotation correctness, and a query count with filters.
- **Back office:**
  - Staff-only access.
  - POST-only actions.
  - Hide reason validation.
  - The filters.
  - "Former staff member."
  - Clearing a restriction: GET shows the confirmation and changes nothing, and POST clears it.
  - No delete action exists.
  - The product delete warning count.
- **Django admin:**
  - The moderation fields are read-only.
  - Admin deletion of a hidden review creates no restriction.
- **Seed:**
  - Every seeded review is eligible.
  - The demo states listed above.
  - The timeline rules (review after order, edit and hide after review, nothing in the future).
  - Two runs at a **frozen clock** produce identical review data, timestamps included.
  - No product has more published reviews than it has distinct customers with a Delivered order for it. No seed test asserts more than 10 reviews on a product.
  - Existing order and dashboard seed tests pass unchanged.
- The suite and Ruff are green at every phase boundary.

### Data safety

- `seed` is never run against the developer's `db.sqlite3` during implementation. It's exercised only through the test suite's isolated test database.
- `db.sqlite3.before-wishlist-backup` is never modified, moved or deleted.
- Before the first `migrate` against `db.sqlite3`, a new backup (`db.sqlite3.before-reviews-backup`) is made, and only with the developer's go-ahead.
- Migrations only add the new app's tables. No existing table is altered, so existing rows are untouched.

### Development workflow

- Each phase is implemented through `/implement`, which delegates to `/tdd`. Both skills' approval checkpoints are kept: the TDD behavior selection, each RED test, each GREEN result, and the manual browser verification before a phase finishes.
- Which behaviors are TDD candidates in each phase is decided in the implementation plan.

## Acceptance Criteria

1. Only a regular customer with a Delivered order for the exact product can create a review. Every other case is refused on the server (anonymous → login, signed in → 403), whatever the template shows.
2. A customer has at most one review per product. A double submit yields one row and no 500 error.
3. Ratings outside 1–5 are rejected by the form and by the database. Comments over 2,000 characters are rejected. Whitespace-only comments are stored as empty.
4. Edits require ownership, current eligibility and published status. "Edited <date>" appears only after a real change, and the review keeps its position.
5. Authors can always delete their own review after confirmation. Deleting a hidden review creates (or updates) a restriction in the same transaction and keeps no rating or comment. Deleting a published review creates none.
6. A restricted customer sees the agreed restriction message for that product, can't create a review there, and can review other eligible products.
7. Hidden reviews never appear publicly and never count toward averages or totals. The author sees "Hidden by staff" with the reason and Delete only.
8. Staff can hide (with a 1–200 character reason) and restore from the Reviews tab under `/backoffice/reviews/`, POST-only, with `hidden_by`/`hidden_at` shown. Repeated actions change nothing. There's no back-office delete.
9. Staff can clear a restriction: GET shows a confirmation page and changes nothing, and only a CSRF-protected, staff-authorized POST removes it.
10. Public pages identify reviewers only as "Verified buyer." No username, email or name appears in public HTML.
11. The detail page and catalog cards show the published-only average (one decimal, half-star visual) and count, or "No reviews yet," with an accessible label. The catalog does this without N+1 queries.
12. The review list is newest first, 10 per page through `?reviews=N`, without JavaScript, with the author's own review pinned once, and with invalid pages handled gracefully. This is proven by fixture tests with at least 11 eligible reviewers of one product, not by seed data.
13. Order status changes never hide, restore or delete a review.
14. Deleting a product or customer cascades to their reviews and restrictions. Deleting a moderator leaves reviews hidden and restrictions active, shown as "Former staff member."
15. The product delete confirmation warns how many reviews will be permanently deleted.
16. `Review` and `ReviewRestriction` are manageable in the Django admin, with moderation fields read-only. Admin deletion creates no restriction.
17. `seed` builds the agreed demo states with valid timelines, is identical across runs at a frozen clock, and leaves existing seeded users, orders and dashboard data unchanged. Every seeded review comes from a customer with a qualifying Delivered order.
18. `uv run pytest` and `uv run ruff check .` pass at every phase boundary. `db.sqlite3` and its wishlist backup are untouched.

## Resolved Constraints

### Seeded pagination: the seed doesn't demonstrate a second page of reviews

- **The original goal:** in Q17, the seed was to give at least one product **more than 10** published reviews, so that review pagination could be shown in the demo.
- **Why it can't be met:**
  - Only regular customers can review, and the seed creates exactly **10** of them: `customer` plus nine background customers (`mwren`, `dcole`, `tokafor`, `lvasquez`, `hpark`, `gfinch`, `snakamura`, `bcrane`, `rmalik`).
  - With one review per customer per product, no product could ever pass 10.
  - The real limit is lower. A replay of the seed's fixed-seed order RNG found that the most distinct customers with a Delivered order for any one product is **five**. That's seraphine-doorbell, recallpro, focusband-workplace-edition, soulsear-authorization-case and seraphine-gen-1. MindSync has four.
- **Decision (developer, 2026-10-18):**
  - The requirement that the seed produce more than 10 reviews for one product is **removed**.
  - The page size stays at **10**.
  - All existing seeded users, orders, RNG sequences and dashboard metrics stay unchanged.
  - The seed stays realistic. Reviews come only from customers with a qualifying Delivered order, so a seeded product has at most five reviews and its list fits on one page.
  - Pagination is proven by isolated pytest fixtures that create at least 11 eligible reviewers, each with a Delivered order for the same product. The development database is never used for this.
- **Rejected alternatives:**
  - Adding seeded reviewer customers would change order counts and dashboard figures (Goal 6, story 40).
  - Lowering the page size conflicts with the approved 10 per page (Q12).

### Confirmed defaults

The developer confirmed these four defaults on 2026-10-18. Each one is already reflected above:

1. `edited_at` is set only when the rating or comment actually changes.
2. The moderation fields (`status`, `hidden_by`, `hidden_at`, `hidden_reason`) are read-only in the Django admin.
3. The edit and delete pages return **HTTP 404** when the signed-in user has no review of the product to act on.
4. If a `ReviewRestriction` already exists for the (user, product) pair, `delete_by_author()` updates it rather than creating a duplicate.

## Out of Scope

Excluded by decisions in this PRD:

- A "Report this review" button and a customer-flagged queue (Q19).
- "Was this helpful?" votes (Q19).
- Staff or merchant replies to reviews (Q19).
- Email notifications for new, hidden or restored reviews (Q19).
- Review photos (Q19).
- Dashboard review metrics; `dashboard/queries.py` is unchanged (Q19).
- A "My reviews" page in the account area (Q19).
- Rate limiting or spam throttling (Q19).
- Catalog sorting or filtering by rating (Q10).
- Ratings on wishlist cards (Q10).
- Review sorting options and HTMX "show more" (Q12).
- Review titles (Q4) and half-star ratings (Q4).
- Public display names (Q11).
- Pre-moderation or a pending-approval queue (Q5).
- Permanent review deletion in the back office (Q6).
- Reviews per order, or more than one review per product (Q3).
- Reviews from staff or the admin (Q2).
- Automatic hiding or restoring when order statuses change (Q8).
- A history log of past hides; restoring clears the current record (Q7).
- Keeping a moderator's username after their account is deleted (Q16).

## Further Notes

- The reviews app deliberately mirrors existing patterns. One row per (user, product) with a named unique constraint follows the cart and wishlist. The filtered list → detail → POST action flow follows the Orders tab. Staff gating follows `StaffRequiredMixin`.
- The repost restriction is the one genuinely new idea. It exists so that "deleting is permanent" and "moderation can't be bypassed" can both be true at once.
- When implementation lands, `CLAUDE.md` should list the `reviews` app and point to this PRD and its plan. That edit is deferred until the developer asks for it.
