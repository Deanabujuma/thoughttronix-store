# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-09-28 — Discount codes: grill interview, build, browser review, code switching

### Prompts
Bracketed labels name the question an answer settled; the prompt text is
verbatim. The work spanned two agent sessions, and prompts are merged in
time order.

1. /grill-me I want customers to enter discount codes at checkout. Expired
   codes should show a clear error. Marketing should create and retire codes
   without engineering help. Retiring a code must not change past orders.
   Coupons must support both whole-order and specific-product discounts.
2. /grill-me Customers can enter discount codes at checkout. Expired codes
   need a clear error message. Marketing can create and retire codes without
   changing past orders. Codes can discount either the whole order or
   specific products.
3. For a product-specific 10% code, does the discount apply only to that
   product while other items stay full price?
4. [Q1, Q2] I choose percentage-only codes for Question 1. For Question 2,
   choose Option 1: discount only eligible products. All matching quantities
   count, and show an error if the cart has no eligible product.
5. [Q3] Option 1, hand-pick products.
6. [Q4] Option 2, with the form requiring at least one product for Selected
   products.
7. [Q5] Option 2: an expiry date plus an Active switch. I agree that Whole
   order with products selected should show a form error.
8. [Q6] Option 1. The code is valid through its expiry date, and the expiry
   date is required.
9. [Q7] Option 2. Use America/Chicago as the store timezone, and check the
   dashboard tests after changing it.
10. [Q8] Option 1. I agree with the suggested check order and shortening long
    product lists.
11. [Q9] Option 2. I agree that code names stay unique after retirement and
    use letters, digits, or hyphens, 3–30 characters.
12. [Q10] Option 2. Keep the order-level and per-line discount snapshots. I
    agree used codes cannot be deleted, only retired.
13. [Q11] Option 1: round each eligible line half-up to cents, then sum the
    line discounts for the order.
14. [Q12] Option 2: whole-number percentages from 1 to 99.
15. [Q13] Option 2: total is the amount paid, and subtotal is calculated from
    total plus discount_amount.
16. [Q14] Option 2: Apply at checkout with an HTMX preview, then validate the
    code again when placing the order.
17. [Q15] Option 1. Use one shared coupon validator and show its errors beside
    the code field. Include the small fix for the existing unavailable-product
    ValueError.
18. end
19. [Q16] I choose the orders app for Coupon. Continue the grill interview one
    question at a time, starting with what Marketing can edit after a code has
    been used.
20. [Q17] Option 2: lock the code, percentage, and eligible products after
    first use, but allow Marketing to change the expiration date or turn it
    off. That keeps the code’s meaning consistent while letting them manage
    the promotion.
21. [Q18] Option 2, including those defaults. Continue to Question 19.
22. [Q19] Option 2 with those defaults. Continue to Question 20.
23. [Q20] Option 1 with those defaults.
24. [Q21] Option 2 with the fixture defaults.
25. [Q22] Option 3. The design is settled. Implement the coupon feature now,
    including tests, and keep the test suite passing at each phase. Do not
    commit or push yet—I need to review the feature first. Leave the final
    PROMPTS.md session log until after review and the required change.
26. Give me a short, step-by-step browser verification plan for the coupon
    feature, including the demo codes and how to check expired codes,
    product-specific discounts, and a past order after retiring its code.
27. During browser review, switching discount codes felt awkward because I had
    to click Remove before I could type another code. Let customers replace an
    applied code directly and click Apply. If the new code is invalid, show its
    error and clear the old discount so the displayed total stays honest. Add
    or update tests, run the suite and Ruff, and do not commit or push yet.
28. Read the standard session-log prompt in the header of PROMPTS.md. Follow it
    to append this coupon session's log, covering the grill interview, initial
    build, browser review, and the later code-switching change. Do not write
    REFLECTION.md and do not commit or push.

### Summary
- **Outcome:** A 22-question grill interview settled the design, recorded in
  `prd/discount-codes.md` and `plans/discount-codes.md`:
  - percentage-only codes from 1–99%, scoped to the *Whole order* or to
    hand-picked *Selected products*
  - a required expiry date (valid through that day, America/Chicago) plus an
    Active switch for retiring
  - one shared validator, `Coupon.objects.redeem`, with a specific message
    per failure
  - order-level and per-line discount snapshots, so retiring or editing a
    code never changes past orders
  - `Order.total` is the amount paid
  - an HTMX Apply preview at checkout, re-checked in `place_order`
  - terms locked after first use, used codes retire rather than delete, and a
    back-office Discount codes tab with status filters and empty states

  The build ran in phases (timezone and the `ValueError` catch, tracer
  bullet, product scope, checkout preview, after-purchase display, back
  office, seed), green at each boundary: 203 → 277 tests, Ruff clean. The
  seed adds four demo codes and leaves the existing 52 orders unchanged. The
  developer committed it as `d602e28`. The agent then wrote a browser
  verification plan, and the developer reviewed the feature in the browser.
  That review found that an applied code was read-only until removed. The
  follow-up change keeps the code field editable with Apply always present:
  - applying over a code replaces it
  - a failed Apply shows its error and clears the old discount
  - a hidden `applied_coupon_code` records the previewed code; if checkout
    receives a different, never-applied code, it re-prices the page instead
    of placing the order (`CouponForm.differs_from_preview`)

  282 tests pass and Ruff is clean. The developer committed the change as
  `31ad7cf`.
- **Deviations:** Every question was answered with the recommended option. The
  developer added details:
  - the rules for product-specific codes (Q2)
  - the store timezone, and asking for a dashboard test check (Q7)
  - the unavailable-product fix, accepted into scope (Q15)

  Prompt 3 was a follow-up question and led to Question 2. Prompt 18 ("end")
  stopped the interview after Q15 and the agent summarized open topics; prompt
  19 answered Q16 and resumed through Q22. Prompt 1's interview was abandoned
  after Q1: that run recommended supporting both percent and fixed-amount
  codes, while the restarted interview (prompt 2) recommended, and the
  developer chose, percentage only. The code-switching change goes beyond the
  literal request: a code typed but never applied is no longer applied
  silently at submit, but re-prices the page first. The agent flagged this
  change in behavior when reporting.
- **Sideways:**
  - The first grill session (prompt 1) stalled after one question, and the
    interview was restarted in a new session.
  - Q20 settled that "the latest Apply wins", but the build made an applied
    code read-only until removed, and the agent never viewed the pages in a
    browser. The developer's browser review caught the gap, and prompt 27
    fixed it.
  - During the build:
    - a scripted template splice landed in the wrong place (fixed by hand)
    - multi-line template text broke exact-text assertions twice (put on one
      line)
    - a scratchpad seed-comparison script needed `PYTHONPATH`
  - During the switching change:
    - Windows Application Control blocked `pytest.exe`, so the suite ran as
      `uv run python -m pytest`
    - two new tests first failed because the input's placeholder contains
      "THOUGHTS10"; the assertions were narrowed
  - Prompts 25 and 27 said not to commit yet; the developer later committed
    both pieces of work themselves.
  - For this log: the session spans two transcripts, and prompt 28 was sent
    to both sessions. The entry was assembled from both transcripts, and
    PROMPTS.md was checked for a duplicate entry before writing (none).

## 2026-09-17 — Product `is_featured` flag and "Featured" storefront badge

### Prompts
1. Add an is_featured field to the Product model. It should be a boolean
   field that defaults to False so existing products remain unfeatured. For
   now, only add the field and whatever migration is needed. Do not add any
   storefront badge yet.
2. Add a "Featured" badge for products where is_featured is True. Show the
   badge both on the catalog listing and on the product detail page. Do not
   change which products are featured yet.
3. Append a session log to PROMPTS.md at the repo root, under today's date,
   newest entry at the top. Record every prompt I gave you this session, in
   order, including any corrections. End the entry with a short summary: the
   outcome, any places where I deviated from a recommended answer or asked
   follow-up questions, and anything that went sideways.
4. Correct today's PROMPTS.md entry to reflect what happened after
   implementation. I manually marked Seraphine, SoulSear Mark I, and SoulSear
   Mark II as featured in Django admin, verified the Featured badge in the
   browser on the catalog and product detail pages, and then ran the full test
   suite with 166 tests passing. Add this correction prompt to the prompt list
   too. Do not change the earlier prompts.

### Summary
- **Outcome:** `Product.is_featured` (`BooleanField(default=False)`) added
  with migration `products/0003_product_is_featured` (a single `AddField`),
  applied locally. A solid `badge badge-accent` "Featured" badge renders on
  catalog cards and on the product detail page (whose badge row gained
  `flex flex-wrap gap-2`). Two view tests cover badge absent/present on each
  page. The agent marked no product as featured; after implementation the
  developer manually marked Seraphine, SoulSear Mark I, and SoulSear Mark II
  as featured in Django admin (local database only — the seed command,
  back-office product form, and querysets are unchanged). The developer then
  verified the badge in the browser on the catalog and product detail pages
  and ran the full suite: 166 passed. Ruff check and format clean.
- **Deviations:** None from a recommended answer, and no follow-up
  questions. The agent offered after prompt 1 to add a PROMPTS.md entry; that
  was left until prompt 3, per the log's rules. Prompt 4 corrected this entry,
  which as first written omitted the developer's post-implementation admin
  changes and browser check.
- **Sideways:** `ruff format --check` flagged the new tests in
  `products/tests.py` after they were written; fixed by running
  `ruff format` and re-running the products tests. The first version of this
  entry described the badge as verified only through tests; the developer
  had since checked it in the browser, which prompt 4 corrected.
