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

## 2026-09-30 — Product images: build, Tailwind fix, browser review, commit

### Prompts
Prompt text is verbatim. Bracketed notes give context and are not part of
any prompt. The build ran across two agent sessions; prompts are in time
order.

1. [Given at the end of the interview session, after its log was written.]
   /handoff the next session implements the design we just agreed.
   Reference the PRD and plan, record that implementation has not started,
   and include the Windows command limitations: use python -m pytest and
   python -m ruff; the Tailwind executable was blocked by Windows
   Application Control.
2. @HANDOFF.md Implement this feature. Read the referenced PRD and plan
   first. After reading the handoff, delete HANDOFF.md; do not commit it.
   Follow the plan and verify each phase. Do not commit or push yet.
3. Apply the migrations, then run import_product_images using the
   project’s Python environment. Do not run seed or reset my database.
   Report the import results, then give me a short browser verification
   plan. Do not commit or push yet.
4. Start the development server using the project’s Python environment.
   Tell me the browser URL.
5. The catalog images load, but their heights differ and the product names
   do not align. Investigate how to rebuild Tailwind using a supported
   build method without disabling Windows security. Preserve the agreed
   4:5 frames and object-contain styling. Do not hand-edit generated CSS.
   Report the available solution before changing the build setup.
6. Yes, apply the official Tailwind executable and pinned official DaisyUI
   plugin setup you tested. Rebuild the CSS, update the README, and run the
   checks. Record this build change in the PRD. Do not commit or push yet.
7. After Ctrl+Shift+R, Calm Collar, CrowdCalm Array, and DreamWeaver still
   have different image heights, and their names do not align. Diagnose
   which stylesheet the browser receives and whether the rendered frame
   markup and CSS enforce aspect-ratio: 4/5. Check for conflicting styles.
   Fix the cause while preserving object-contain and showing each whole
   image. Do not commit yet.

   [During this request the agent launched the Claude in Chrome skill; I
   declined to install the extension.]
8. Continue without the browser extension. Check whether the image’s
   natural size or the card’s flex layout expands the 4:5 wrapper. Fix the
   frame sizing while keeping the whole image visible with object-contain.
9. Create a 400×400 PNG named too-small.png on my Desktop for an upload
   rejection test. Do not change project code.
10. Create a plain text file on my Desktop named fake-image.png. Put “This
    is not an image” inside it. Do not change project code.
11. [The session resumed here.] Browser review update: the too-small and
    fake-image uploads were rejected. A valid upload saved, and removing it
    restored Seraphine Mini’s placeholder.

    When I tried removing Hush’s image and uploading a new image together,
    the product saved instead of showing the conflict error. Investigate
    whether I submitted both choices correctly or whether the form has a
    bug. Fix it if confirmed and run the tests. Do not commit or push.
12. [I pasted the agent's previous reply, then wrote:] Help me manually
    test Hush’s missing-image fallback. Temporarily rename its card.webp
    file to card.webp.bak, keeping the original safe. Do not change the
    database, run seed, or commit anything. Tell me when to refresh the
    catalog. Wait for my confirmation before restoring the file.
13. I confirmed Hush’s catalog card shows the placeholder. Restore
    card.webp.bak to card.webp now and verify the real card image loads
    again. Do not commit or push.
14. Review the product-images diff against the PRD and plan. Run python -m
    pytest, python -m ruff check ., and python manage.py check. Confirm
    media/, product-images/, and HANDOFF.md will not be committed. Report
    any remaining issues and git status. Do not commit or push yet.
15. Add a short “Amended during build” note to PRD Q5 documenting the final
    image-frame changes. Add HANDOFF.md to .gitignore and document the
    Tailwind --force rebuild command in README.md. Then commit the
    product-images feature with the message "Add uploaded product images"
    and push. Keep media/ and product-images/ untracked. Leave the build
    session log and reflection for the final documentation commit.
16. I created Lucent through the back-office form and verified its detail
    page. Find the following for my reflection:
    1. Product’s ImageField line, with filename and line number.
    2. The upload form’s opening <form> tag, with filename and line number.
    3. Lucent’s image path on disk, image value in the database, and
       displayed detail-image URL.
    4. The settings and development URL code that determine those paths.

    Explain briefly, but do not write my reflection or run seed.
17. Read the PROMPTS.md header and show me its exact standard session-log
    prompt. Do not edit files yet.
18. Append a session log to PROMPTS.md at the repo root, under today's date,
    newest entry at the top. Record every prompt I gave you this session, in
    order, including any corrections. End the entry with a short summary:
    the outcome, any places where I deviated from a recommended answer or
    asked follow-up questions, and anything that went sideways.

    Preserve the interview log and all older entries. Include the resumed
    portion of this build session. Distinguish my browser confirmations from
    your automated checks.

    Also record this image-generation disclosure: [the tool, product, and
    exact image prompt are recorded under "AI image disclosure" below]

    Do not invent prompts or confirmations you cannot recover. Do not change
    REFLECTION.md, commit, or push yet.

### AI image disclosure
- **Tool:** ChatGPT’s built-in image-generation tool.
- **Product:** Lucent, added by me through the back-office create form.
- **Exact image prompt:** “Create a photorealistic premium product
  photograph for the fictional ThoughtTronix catalog. Product: Lucent, a
  futuristic neural focus headband. A sleek silver titanium headband with an
  elegant continuous soft cyan-blue illuminated ring and subtle neural
  sensor pads, shown alone at a three-quarter angle on a dark navy display
  pedestal. Cinematic studio lighting, realistic brushed metal, restrained
  futuristic design, dark navy background matching a night-themed
  storefront. Portrait 4:5 composition, entire headband clearly visible with
  generous margins, sharp product details. No people, no text, no logo, no
  watermark. Generate at least 1024 pixels on the shortest side.”

### Summary
- **Outcome:** `plans/product-images.md` was built phase by phase, with
  the suite green at each boundary (282 → 328 tests). The work was
  committed and pushed as `d32d9f1` "Add uploaded product images" (26
  files).
  - Upload validation with the PRD's messages, and the original plus WebP
    card and detail copies built during validation.
  - Random-ID folders, with cleanup only after commit (bulk deletes
    included) and emptied folders removed.
  - 4:5 `object-contain` card frames, lazy catalog images, stored detail
    dimensions, and alt text with placeholder and missing-file fallbacks.
  - The back-office preview, Remove image, and thumbnails, and
    `import_product_images`, which attached 12 of 34 products.
  - The build moved to the official Tailwind v4.3.2 CLI and DaisyUI's
    pinned v5.7.47 plugin file, because Smart App Control blocks the
    unsigned fork.
  - The frame gained a visible border, an out-of-flow image, and
    `basis-full` on the catalog link.
  - Kept out of git: `media/`, `product-images/`, `HANDOFF.md`, and the
    generated `tailwind.css`. This entry and REFLECTION.md are left for the
    final documentation commit.
- **My browser confirmations:**
  - The catalog images loaded, but heights and names looked misaligned
    (reported twice).
  - After the frame fixes, I confirmed the corrected catalog frames looked
    aligned.
  - `too-small.png` and `fake-image.png` were rejected.
  - A valid upload saved, and Remove image restored Seraphine Mini's
    placeholder.
  - I first reported that removing Hush's image and uploading a new one
    together saved the product. When I retested with Remove image switched
    on and a new file selected, I saw the expected conflict message, and
    the existing image stayed.
  - Hush's catalog card showed the placeholder while `card.webp` was
    renamed.
  - I created Lucent through the back office and verified its detail page.
  - I confirmed Lucent appears in the catalog with its headband image.
- **Agent's automated checks (not browser confirmations):**
  - pytest, ruff, `manage.py check`, and `makemigrations --check` at each
    phase and before the commit.
  - All 13 supplied images run through `process_upload` in memory.
  - The served CSS and media checked over HTTP.
  - Headless Edge (DevTools protocol) measurements of the card frames at
    several widths, including stress tests: overflow visible, the link's
    width utility removed, and the image forced to its natural height.
  - A headless Edge reproduction of Remove plus file, in both orders,
    against an isolated copy of the database and media on port 8001: the
    form showed the conflict error and saved nothing.
  - Checksums on the `card.webp` rename and restore.
- **Deviations and follow-ups:**
  - I asked for a report on a supported Tailwind fix before any build
    change, then approved the official CLI plus pinned plugin.
  - Twice I followed up on frame alignment after the agent's measurements
    showed equal frames. The first follow-up led to the visible border; the
    second asked whether natural size or flex layout expands the wrapper,
    which led to the out-of-flow image and `basis-full`.
  - For the Hush conflict report, the agent found no form bug, so no code
    changed.
  - I asked for the Desktop test files, the manual fallback test, a review
    before committing, and the code locations for my reflection.
- **Sideways:**
  - A shell heredoc wrote a raw NUL byte into `conftest.py`. A grep
    reporting "Binary file" caught it.
  - The "transparent" test PNG was fully opaque, so its test failed until
    the fixture was given real transparency.
  - `BoundField.value()` returns `None` for uploads, so the "select the
    file again" note never showed; it now uses `.data`.
  - Deleting image files left empty folders behind, which a test caught.
  - The Django admin was an unvalidated upload path; its image fields are
    now read-only.
  - The first real import crashed printing `←` on the cp1252 console,
    after Seraphine had already imported. The arrow was replaced and a
    regression check added. The rerun skipped Seraphine and imported the
    other 11.
  - The first rebuild with the official CLI produced 401 KB of CSS because
    Tailwind scanned `daisyui.mjs` for class names. `@source not` fixed it
    (111 KB).
  - `tailwind build` skipped a rebuild after template-only changes; `--force`
    is now in the README.
  - The first frame diagnosis found correct 4:5 frames with invisible
    letterboxing, so the border was added. The later stress test showed the
    frame's width depended on the link's `w-full`.
  - Headless Edge rejected the first DevTools connection over its Origin
    header. The client was changed to send none, rather than loosening
    Edge's origin rules.
  - Mid-investigation, the agent's progress note said "Confirmed the bug"
    when the browser reproduction had actually shown the form working.
    The final report correctly concluded there was no bug.

## 2026-09-30 — Product images: grill interview, PRD, and plan (no implementation)

### Prompts
Bracketed labels name the question an answer settled; the prompt text is
verbatim.

1. /grill-me I want employees to upload real product images through the
   back office and display them on the catalog and product detail pages. The
   supplied images are in product-images/ at the repository root. Every
   product must show its uploaded image when available or its existing
   category placeholder. Unusable uploads must be rejected before saving,
   with a clear explanation. Help me decide accepted formats, file size
   limits, image consistency, storage, and page performance. Ask me
   questions one at a time before implementing anything.
2. [Image folder] The supplied images are now in product-images/ at the
   repository root. Please inspect them and continue the grill-me interview.
   Ask one question at a time, and do not implement anything yet.
3. [Q1] Option 1: one optional image per product, with the existing category
   placeholder when no image is available.
4. [Q2] Option 1: accept JPEG, PNG, and WebP. Validate the actual file
   contents, not just the extension. Reject unsupported or corrupt files
   before saving, with a clear message explaining which formats are
   accepted.
5. [Q3] Option 2: a 5 MB upload limit. Reject larger files before saving,
   with a message showing the file’s size and the 5 MB maximum. Keep the
   limit in one named setting or constant.
6. [Q4] Option 3: require at least 800 pixels on the shortest side and no
   more than 6000 pixels on the longest side. Reject images outside those
   limits before saving, with a clear message showing their dimensions and
   the required limits.
7. [Q5] Option 2: use a consistent 4:5 frame on catalog cards with
   object-contain so the whole image remains visible. Apply the same frame
   to placeholders and use a background consistent with the site theme. On
   detail pages, show the whole image in its original proportions without
   cropping.
8. [Q6] Option 1: use Django’s standard local media storage, with MEDIA_ROOT
   pointing to the repository’s media folder and MEDIA_URL set to /media/.
   Ignore media/ in Git and serve it through Django only when DEBUG is True.
   Keep product-images/ as temporary source material, separate from
   uploaded media.
9. [Q7] Option 2: keep the original and generate two WebP display copies
   when saving: a catalog copy fitting within 640×800 and a detail copy
   fitting within 1200×1500, at quality 80. Preserve proportions without
   cropping or enlarging small images. If processing fails, reject the
   upload with a clear message and preserve any existing image.
10. [Q8] Option 2: delete the old original and both display copies only
    after the database change successfully commits. Apply this to
    replacement, clearing an image, and deleting a product. A failed upload
    or save must preserve the existing image and its files.
11. [Q9] Option 3: use a separate import_product_images command to attach
    the supplied images to existing products through the same validation and
    processing as employee uploads. Keep product-images/ temporary and
    uncommitted. Report missing or rejected files clearly, and leave those
    products showing their placeholders.
12. [Q10] Option 1: SyncRest uses "SyncRest GPT No Text.png", and SoulSear
    Mark I uses "SoulSear No Text.png". Keep the ten clear matches listed
    above. Report the unused SyncRest text version as unmapped, not as an
    error.
13. [Q11] Option 3: Skip products that already have an image by default. Add
    a --replace flag for intentional replacement, and report imported,
    skipped, missing, rejected, and unmapped files.
14. [Q12] Option 1: Lazy-load catalog images, load the detail image
    immediately, and store the detail copy’s width and height for its img
    tag. Keep category placeholders inside the same 4:5 catalog frames we
    agreed on.
15. [Q13] Option 3: Use the styled upload with a current-image preview, a
    Remove image checkbox, and clear upload rules. Add thumbnails to the
    back-office product list. If validation fails, explain that the employee
    must select the file again and that the existing image is unchanged.
16. [Q14] Option 1: Reject the conflicting submission and keep the existing
    image unchanged. Say: “Choose a new image or tick Remove image, not
    both. If uploading, please select the file again.”
17. [Q15] Option 3: Add an optional image_alt field with help text
    explaining how to describe the image. When blank, use the generated
    fallback text from option 2. When displaying a placeholder, always use
    the category placeholder description.
18. [Q16] Option 2: Put the shared image validation, processing, and cleanup
    helpers in products/images.py, with docstrings and type hints. Update
    only the relevant architecture statement in CLAUDE.md to include this
    third module. Do not add unrelated guidance.
19. [Q17] Option 1: Generate test images in memory with Pillow and use an
    automatic temporary MEDIA_ROOT fixture. Test the import command using a
    temporary source folder.

    Correction: existing product tests do call seed, as the earlier audit
    confirmed. Ensure those tests also use temporary media storage.
20. [Q18] Option 3: Use a unique random ID folder for each upload under
    products/, containing original.<ext>, card.webp, and detail.webp. Clean
    up old files only after the database change commits successfully.

    Also remove the false “tests never invoke the seed command” statement
    from the conftest.py docstring.
21. [Q19] Option 1: Create prd/product-images.md and
    plans/product-images.md, keeping them concise. Add only a short
    reference in CLAUDE.md. Use the standard prompt in the PROMPTS.md header
    to log this interview accurately, preserving existing entries.

    First recap all decisions for me to review. Do not begin implementation
    yet.
22. [Recap] I approve the recap and listed defaults, with these
    clarifications:

    - If an uploaded image or its display copy is missing from storage, show
      the existing category placeholder instead of a broken image. Include
      tests for missing files.
    - Add Pillow to pyproject.toml and update uv.lock.
    - Create only the PRD, plan, short CLAUDE.md references, and interview
      log now. Do not implement yet. The assignment requires a handoff and a
      fresh session before implementation.

    After writing those documents, stop and let me review them.

### Summary
- **Outcome:** A 19-question grill interview settled the design, recorded in
  `prd/product-images.md` and `plans/product-images.md`:
  - one optional image per product, falling back to the category
    placeholder, including when a stored file is missing
  - JPEG/PNG/WebP by detected content, 5 MB, 800–6000 px, each rejected
    before saving with a specific message
  - the original is kept, plus WebP card (640×800) and detail (1200×1500)
    copies built during validation, stored in a random-ID folder per upload
  - old files are deleted only after commit, on replace, clear, and delete
    (bulk deletes included)
  - a 4:5 `object-contain` card frame, lazy catalog images, stored detail
    dimensions, and an optional `image_alt`
  - `products/images.py` as a third deep module
  - a separate `import_product_images` command with an explicit 12-product
    mapping and `--replace`
  - Pillow-generated test images and an autouse temporary `MEDIA_ROOT`

  Only documents changed. `CLAUDE.md` got the PRD/plan reference line.
  Adding Pillow and updating `uv.lock`, and changing the architecture
  statement to three deep modules, are Phase 0 and Phase 1 of the plan, so
  they happen in the implementation session.
- **Deviations:** Q9 chose a separate import command over the recommended
  `seed` integration, keeping `product-images/` uncommitted. Q5 asked for a
  theme background instead of the placeholders' fixed hex colour. Q17
  corrected the claim that tests never call `seed`. Q18 added removing that
  false docstring line. The recap approval added the missing-file fallback
  and its tests.
- **Sideways:** `product-images/` did not exist when the session started,
  so the first question asked where the images were. A scratch script named
  `inspect.py` shadowed the standard library and was renamed. I trusted the
  `conftest.py` docstring's "tests never invoke the seed command"; the user
  caught this, and `products/tests.py` confirmed both seed tests. The
  SoulSear file had no mark number, so the mapping to Mark I was inferred
  from the product copy and confirmed by the user.

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
