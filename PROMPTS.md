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

## 2026-10-18 — Product reviews Phase 6: demo reviews in the seed

### Prompts
The same agent session as the Phase 5 entry below, which records its own
prompts 1–18. Prompt text is verbatim, missing spaces after full stops
included. Prompts 1–3 staged, committed and pushed Phase 5; they are
recorded here because that entry was already committed. Every prompt in
this entry was typed directly, so `/implement` never ran as a command and
the agent followed it and `/tdd` directly.

1. I approve staging exactly the 17 proposed Phase 5 files, including the
   new migration.Stage only the approved paths. Do not use git add . or
   git add -A.Show the staged file list, diff summary, and Git
   status.Verify that db.sqlite3, all three backups, generated CSS, and
   unrelated files remain excluded.Do not commit or push yet. Stop for my
   final approval.Proposed commit: feat(reviews): add Phase 5 hidden
   review restrictions
2. I approve committing the 17 staged Phase 5 files.Use the commit
   message:feat(reviews): add Phase 5 hidden review restrictionsDo not
   stage any additional files or include the database, backups, or
   generated CSS.After committing, report the commit hash and Git
   status.Do not push or begin Phase 6 yet. Stop for my separate approval.
3. I approve pushing commit 4fe2b56 to origin/main.First confirm a safe
   fast-forward, then push normally.Do not create another commit,
   force-push, or stage additional files.Confirm GitHub is synchronized
   and report Git status.Preserve my development database, all three
   backups, and existing reviews.STOP after the push. Do not begin Phase 6
   yet.
4. Begin Phase 6: Demo Data and Final Verification.Review the PRD, plan,
   seed command, and existing tests.Propose up to three TDD behaviors
   covering eligible demo reviews, deterministic and repeatable seeding,
   and preservation of existing demo data and dashboard metrics.STOP for
   my approval before writing code.Do not run seed, reset, or migrations
   on my development database. Preserve my existing reviews and all three
   backups. Do not stage, commit, or push.
5. I approve Phase 6's two TDD behaviors, the characterization test first,
   and all seven design decisions.Begin with the seed-data
   characterization test only.Use pytest's isolated database and a fixed
   clock. Record the existing orders, coupons, carts, wishlists,
   addresses, and dashboard metrics.Show the baseline and prove the test
   passes before changing seed.py.STOP for approval before Behavior 1
   RED. Do not run seed against my development database or change any
   backups.
6. I approve the Phase 6 characterization test.Begin Behavior 1 RED
   only.Test that seeded reviews come exclusively from eligible
   Delivered-order customers, contain no duplicate customer/product
   pairs, and demonstrate the approved published, edited, hidden, and
   restricted states.Use the existing fixed clock and isolated pytest
   database.Demonstrate a genuine failing assertion, then STOP before
   GREEN.Preserve the baseline test, development database, all three
   backups, and existing reviews.
7. I approve Behavior 1 RED.Implement Behavior 1 GREEN only using eligible
   Delivered-order customers and a separate deterministic review RNG.Keep
   the existing demo data and dashboard metrics unchanged.Run the review
   test, baseline test, existing seed tests, and Ruff checks.STOP for
   approval before Behavior 2 RED.Do not modify my development database,
   backups, or existing published reviews. Do not stage, commit, or push.
8. Behavior 1 GREEN is approved. Leave the placeholder timestamps
   unchanged.Proceed directly to Behavior 2 RED, testing timeline
   correctness and repeatable seed output.Show the failing assertion,
   confirm the previous tests still pass, and stop before GREEN.
9. I approve Behavior 2 RED.Implement the approved timestamp offsets,
   explicitly saving them rather than relying on Django's default
   clock.Verify that the complete set of seeded reviews and restrictions
   is identical across repeated runs.Keep all existing demo data and
   dashboard metrics unchanged.STOP for GREEN approval. Do not stage,
   commit, push, or modify my development database.
10. I approve Behavior 2 GREEN.Finish the remaining Phase 6 work: seed
    cleanup, updated success message, README demo instructions, and
    PROMPTS.md documentation.Run the full test suite, Ruff, Django checks,
    and migration checks.Show the exact proposed Git staging list.Do not
    stage, commit, or push yet. Preserve my development database, existing
    reviews, and all three backups.Stop for approval.

### Summary
- **Outcome:** `seed` builds a demo world with reviews in every state:
  - 47 reviews: 40 published, 7 hidden, 13 edited;
  - 1 restriction;
  - all from customers who received the product.

  It's identical every run at the same clock, and it leaves every existing
  order, discount code, cart, wishlist, address and dashboard figure
  exactly as it was. Phase 6 was verified only in pytest's isolated
  database, as approved in the plan; `seed` never ran against
  `db.sqlite3`.
  - **Phase 5 commit (prompts 1–3):** the 17 reviewed files, including
    `0002_reviewrestriction.py`, were staged by path and committed as
    `4fe2b56`, a new commit on top of `340bd51`. It was pushed to
    `origin/main` as a fast-forward.
  - **Planning (prompts 4–5):**
    - **Two TDD behaviors, not three.** The developer's third area,
      preserving existing data, already held, so it couldn't start RED. It
      became a **characterization test** written before any seed change.
    - **Seven decisions,** all approved: freezing the clock by
      monkeypatching `timezone.now` (no new dependency); a separate review
      RNG drawn last; a fixed list of comments; fixed date offsets; hidden
      fields set directly; a restriction row with no review behind it; and
      automated-only verification.
  - **The characterization test (prompt 5):** `products/test_seed_baseline.py`
    seeds at a frozen 2026-10-18 17:00 UTC and snapshots, by natural keys,
    every order and its lines, the discount codes, the customer's cart,
    wishlist and addresses, all users, and the five dashboard queries. The
    canonical-JSON SHA-256 recorded before any change is `7d389c62…bfba774`.
    The snapshot has 52 orders and 109 lines, and the dashboard shows
    $57,395.20 from 47 sales. Readable figures are asserted before the
    digest. Two throwaway probes, since deleted, showed the digest is
    stable across runs and changes when a single cent changes.
  - **TDD (prompts 6–9):** two approved behaviors, each RED on an
    assertion, then GREEN:
    1. **Genuine reviews in every demo state.** Every author is a regular
       customer with a Delivered order for that exact product; there are
       no duplicate pairs and no product has more reviews than its
       Delivered customers. The demo `customer` has MindSync published and
       edited, DreamWeaver hidden by `employee`, and SyncRest, Seraphine
       Mini and Veil unreviewed. Background customers have a mix, and
       there's exactly one restriction, on a background customer with no
       review left. RED: `assert 0 > 0`. GREEN: `_create_reviews()` with
       `random.Random(1716)`, run after every order and coupon draw;
       fixed reviews for `customer`; for background customers, one
       decision per (customer, product) pair at its first Delivered order;
       and the restriction on the first pair left unreviewed (`gfinch` on
       seraphine-gen-1). The baseline digest was unchanged.
    2. **A valid timeline, and the same output every run.** Each review is
       posted after its order and before `now`; edits and hides come after
       posting; the restriction runs order < hide < restriction < `now`;
       all timestamps are aware; and two runs give identical data.
       Behavior 1's dates were deliberately left as placeholders so this
       RED would be real. GREEN set every timestamp explicitly, using
       `POSTED_AFTER_ORDER` (2 days), `EDITED_AFTER_POSTING` (3 days),
       `HIDDEN_AFTER_LAST_CHANGE` (1 day) and `RESTRICTED_AFTER_HIDING`
       (1 day), through one `_create_review()` helper.
  - **Normal Phase 6 work (prompt 10):**
    - `_wipe()` deletes every restriction, then every review, explicitly.
    - The success message adds "47 reviews (7 hidden) and 1 review
      restriction.", using `pluralize`.
    - The seed's docstring describes the reviews.
    - The README has a **Demo reviews** section: what `customer` sees on
      each product, the back-office Reviews and Restrictions pages, and a
      note that no seeded product fills a second page.
    - Three tests: the wipe removes reviews and restrictions the seed
      doesn't manage; review counts are stable over two runs; and the
      success message is right.
    - The suite went from 778 to 784.
- **Deviations:**
  - The third requested TDD behavior became a characterization test, as
    proposed and approved.
  - **The hide date rule was refined.** Decision 4 said "hide = review + 1
    day". The agent made it 1 day after the review's *last change*, so a
    hide can never come before an edit, which hidden reviews can't have in
    the app. No seeded review is both edited and hidden, so no date
    changed. This was flagged before it was implemented.
  - There was no browser verification, by the plan's decision: running
    `seed` on `db.sqlite3` would wipe the developer's real reviews.
  - The `CLAUDE.md` update for the `reviews` app is still deferred, as the
    PRD says, until the developer asks.
- **Sideways:**
  - **The model's default clock ignores the test's clock.** Behavior 2's
    RED showed the placeholder `created_at` at the real time (01:14 UTC,
    Oct 19), not the frozen 17:00. `default=timezone.now` was captured when
    the model loaded, so monkeypatching didn't reach it. That meant
    Behavior 1's placeholders weren't actually repeatable. Behavior 2's
    explicit timestamps fixed it.
  - **Ruff and the shared clock fixture.** Taking the imported
    `frozen_clock` fixture as a test argument triggered Ruff `F811`. The
    tests use `@pytest.mark.usefixtures("frozen_clock")` instead, leaving
    the baseline file untouched. Ruff's `--fix` later merged the two
    imports from it.
  - **A probe that couldn't find its fixture.** The first baseline probe
    errored because it didn't import `frozen_clock`. That was fixed in the
    probe, before any value was recorded.
  - **An inaccurate docstring.** The new seed-review test file's docstring
    claimed every run used the frozen clock; it was corrected.

## 2026-10-18 — Product reviews Phase 5: restrictions after deleting a hidden review

### Prompts
The same agent session as the Phase 4 entry below, which records its own
prompts 1–12. Prompt text is verbatim, typos and missing spaces included.
Prompts 1–5 staged, committed and pushed Phase 4; they are recorded here
because that entry was already committed. Prompts 3, 4 and 7 repeated
earlier text and are described rather than reproduced. Prompts 9, 10, 12
and 14–18, and the short addition in prompt 7, were typed directly; the
rest were pasted in. `/implement` never ran as a command, so the agent
followed it and `/tdd` directly.

1. I approve the proposed 12-file staging list for Product Reviews Phase 4.

   Stage ONLY these exact paths:
   PROMPTS.md
   reviews/forms.py
   reviews/models.py
   reviews/urls.py
   reviews/views.py
   templates/backoffice/base.html
   templates/reviews/partials/_reviews_section.html
   templates/reviews/manage_reviews.html
   templates/reviews/manage_review_detail.html
   templates/reviews/partials/_moderation_status.html
   reviews/test_backoffice.py
   reviews/test_models.py

   Do not use git add . or git add -A.

   After staging, show git diff --cached --name-only, git diff --cached
   --stat, and git status --short. Verify there are exactly 12 staged
   files, with no database, backup, generated CSS, or unrelated files
   included.

   Do not commit or push yet. Stop for my final review of the staged
   changes.

   Proposed future commit message: feat(reviews): add Phase 4 staff
   moderation.
2. I give final approval to commit the 12 staged Product Reviews Phase 4
   files.

   Use this exact commit subject:
   feat(reviews): add Phase 4 staff moderation

   You may include the repository's usual co-author trailer.

   Do not stage additional files, amend previous commits, or include
   db.sqlite3, db.sqlite3.before-reviews-backup,
   db.sqlite3.before-wishlist-backup, or generated CSS.

   After committing, report the full commit hash, git log -1 --oneline,
   and git status --short. Confirm exactly the 12 approved files were
   committed, and all database files remain excluded.

   Do NOT push to GitHub yet. Stop for my separate push approval. Do not
   begin Phase 5.
3. *(Prompt 2 sent again, word for word, after the commit existed.)*
4. *(A copy of prompts 2 and 3 and the agent's two replies, pasted back
   with no new instruction.)*
5. That second instruction was intended as a verification checkpoint to
   confirm the operation was idempotent. Since the Phase 4 commit already
   existed, I wanted to ensure that repeating the instruction wouldn't
   create a duplicate commit, amend the existing one, or stage additional
   files.

   The correct behavior was to recognize that the requested state had
   already been achieved, verify the commit hash and working tree, and
   stop without making further changes.

   That check passed. We can now proceed with the separately approved
   push.
6. Phase 4 was successfully pushed to origin/main at commit
   340bd51c988f46d4df5d91ae77539554ca957aa9. Begin ONLY Phase 5 of the
   approved Product Reviews PRD and plan: hidden review restrictions.

   Read prd/product-reviews.md, plans/product-reviews.md,
   .claude/skills/implement/SKILL.md, and .claude/skills/tdd/SKILL.md
   before proposing work.

   Before writing any implementation or tests, propose up to three Phase 5
   TDD behaviors for my approval. Cover: (1) deleting a HIDDEN review
   creates or preserves a restriction for that exact customer/product and
   prevents posting again, without restricting other products; (2)
   deleting a PUBLISHED review does not restrict re-reviewing when
   eligible; and (3) staff-only, CSRF-protected restriction clearing via a
   GET confirmation and POST action, restoring eligibility appropriately.
   Include atomicity, repeated delete/clear handling, authorization, and
   the UI effects required by the PRD.

   Identify any open design decisions and explain the RED/GREEN order.
   STOP for my approval before writing code.

   The database schema may require a migration. Do not create or apply
   migrations yet. Before any migration touches the development database,
   stop to confirm the existing backup and obtain explicit approval. Never
   overwrite either backup.

   Preserve db.sqlite3 and both backups, including the real published
   MindSync and SyncRest reviews. Use pytest's isolated test database for
   fixtures. Do not seed, reset, stage, commit, push, or begin Phase 6.
7. *(Prompt 6 arrived twice more: once while the agent was still working
   on it, and once with this short version added.)* Begin Phase 5: Hidden
   Review Restrictions.Review the approved PRD, plan, and TDD
   workflow. Propose up to three behaviors covering hidden-review deletion
   restrictions, normal published-review deletion, and staff clearing
   restrictions.Stop for my approval before writing code.Preserve the
   existing database and backups. Do not create or apply migrations yet,
   or stage, commit, push, or begin Phase 6.
8. I approve the three Phase 5 TDD behaviors, their order (1 → 2 → 3), and
   the recommended design decisions described in your proposal.

   I explicitly authorize creating
   reviews/migrations/0002_reviewrestriction.py for pytest's isolated test
   database, but NOT applying it to db.sqlite3. Generate and inspect the
   migration using the isolated/in-memory configuration. Do not run
   migrate against my development database.

   Proceed with Phase 5 Behavior 1 RED ONLY: deleting a hidden review
   creates or updates exactly one restriction for that customer/product in
   the same transaction, preserving the moderation reason, moderator and
   timestamp but not the review rating/comment. Deleting a published review
   must not create a restriction and must continue to permit an otherwise
   eligible customer to review again.

   Create the minimum ReviewRestriction model and migration skeleton
   required for an assertion-based RED test. Add focused isolated pytest
   cases for the hidden and published deletion paths, the
   one-restriction-per-user/product uniqueness rule, and the expected
   atomicity/idempotence behavior. Demonstrate a genuine failing assertion
   rather than an import, migration, or missing-table error. STOP for my
   RED approval before implementing GREEN or starting Behavior 2.

   Before any future migration is applied to db.sqlite3, stop and request
   approval to create and verify a NEW backup named
   db.sqlite3.before-restrictions-backup. Never overwrite either existing
   backup.

   Preserve db.sqlite3, both existing backups, and my published MindSync
   and SyncRest reviews. Do not seed, reset, stage, commit, push, or begin
   Phase 6.
9. I approve Behavior 1 RED: three expected assertion failures and three
   passing cases.Proceed with GREEN for Behavior 1 only.Implement the
   hidden-review deletion and restriction creation as one atomic operation.
   Preserve the staff moderation record, prevent duplicate restrictions,
   and keep published-review deletion unchanged.Run the targeted tests,
   rollback regression, full test suite, and Ruff.STOP for GREEN approval
   before Behavior 2. Do not apply the migration to my development
   database, or stage, commit, or push anything.
10. I approve Behavior 1 GREEN. All 749 tests pass.Proceed with Behavior 2
    RED only.Test that a restriction blocks review creation for the
    specific product on both GET and POST, and displays the approved
    restriction message instead of Write a review.Verify other eligible
    products are unaffected and forbidden requests cannot create
    reviews.Show the expected failing assertions, then STOP before
    GREEN.Keep the migration off my development database and preserve all
    existing reviews and backups.
11. I approve Phase 5 Behavior 2 RED.Proceed with GREEN for Behavior 2
    only.- Block restricted customers from both GET and POST review
    creation with HTTP 403.
    - Display the approved restriction message instead of Write a review.
    - Keep reviews of other eligible products available.
    - Preserve existing authentication, eligibility, uniqueness, and CSRF
    protections.
    Run the focused tests, full suite, and Ruff. STOP for GREEN approval
    before Behavior 3.Do not migrate the development database, stage,
    commit, push, or change either existing review.
12. I approve Behavior 2 GREEN. All 750 tests pass.Proceed with Behavior 3
    RED only.Test that staff can clear a restriction through a
    confirmation page and CSRF-protected POST, while customers cannot.
    Verify the restriction is removed only when authorized and that the
    customer can review again afterward.Show the expected failing
    assertions, then STOP before GREEN.Do not migrate my development
    database, modify my existing reviews, or stage, commit, or push
    anything.
13. I approve Phase 5 Behavior 3 RED, including all 10 cases and both
    proposed messages.Proceed with GREEN for Behavior 3 only.- Secure the
    Restrictions list and clear action with StaffRequiredMixin.
    - Keep GET confirmation-only and require CSRF-protected POST to clear.
    - Display the approved success or repeated-clear message.
    - Preserve unrelated restrictions and restore review eligibility
    appropriately.
    Run the targeted tests, full suite, and Ruff.STOP for GREEN approval
    before the remaining Phase 5 work. Do not migrate the development
    database or stage, commit, or push.
14. I approve Phase 5 Behavior 3 GREEN. All 760 tests pass.Complete the
    remaining Phase 5 work: Restrictions dashboard, admin safeguards,
    product deletion warning, regression tests, and final checks.Then STOP
    before applying the database migration. Request approval to create and
    verify a new, separate restrictions backup first.Preserve my existing
    reviews and database. Do not stage, commit, push, or begin Phase 6.
15. I approve creating only db.sqlite3.before-restrictions-backup.I'll stop
    the development server first.Check that the destination doesn't exist,
    then create the backup without overwriting anything.Verify the source
    and backup have identical SHA-256 hashes and report their
    sizes.Preserve my two existing backups and published MindSync and
    SyncRest reviews.STOP after backup verification. Do not run
    migrations, stage, commit, or push.
16. I've stopped the Django development server.Check again for running
    Django processes. If any remain, report them and stop.If none remain,
    create and verify db.sqlite3.before-restrictions-backup without
    overwriting anything.Confirm matching SHA-256 hashes and preserve both
    older backups.Do not run migrations or Git operations yet.
17. I approve applying the Phase 5 migration.First run uv run python
    manage.py migrate --plan.Only if the plan shows exactly
    reviews.0002_reviewrestriction, run uv run python manage.py
    migrate.Then verify the new restrictions table exists and is empty,
    database integrity is OK, and both published reviews remain
    unchanged.Preserve all three backups.STOP after verification. Do not
    stage, commit, push, or begin Phase 6.
18. Phase 5 browser verification passed, including the customer 403
    check.Complete the Phase 5 PROMPTS.md documentation and rerun all
    final tests, Ruff, and Django checks.Show the exact proposed Git
    staging list and diff summary, including the new migration file.Do not
    stage, commit, or push yet. Exclude the development database, all
    three backups, and generated CSS.Stop for approval before Phase 6.

### Summary
- **Outcome:** an author who deletes a review staff hid can't simply post
  it again. A restriction stays behind for that product until staff clear
  it, and the customer's other products are unaffected.
  - **Phase 4 commit (prompts 1–5):** the 12 reviewed files were staged by
    path and committed as `340bd51`, a new commit on top of `0cd0a12`.
    - **The repeated commit request (prompt 3):** the agent checked the
      state read-only and stopped, with no second commit, amend or
      staging. In prompt 5 the developer explained it was a deliberate
      idempotency check.
    - **The push:** to `origin/main` as a fast-forward after a fresh
      fetch.
    - **A saved memory:** the agent recorded the rule — verify an
      already-done instruction and change nothing — in its project memory.
  - **Planning (prompts 6–8):** three behaviors, in order 1 → 2 → 3, and
    ten decisions, all approved. Among them:
    - a restricted create URL gets 403;
    - the restriction message wins over "ineligible";
    - clearing a missing restriction redirects with an info message, not
      a 404;
    - the Restrictions page sits under the Reviews tab;
    - the admin has no Add for restrictions;
    - the delete warning counts every review.

    The developer's item 2, "deleting a published review doesn't
    restrict", already worked from Phase 2, so it became a case inside
    Behavior 1. Creating, not applying, `0002_reviewrestriction.py` was
    explicitly authorized (prompt 8), because the RED test needs the table
    in pytest's database.
  - **TDD (prompts 8–13):** three approved behaviors, each RED on an
    assertion, then GREEN with the full suite run:
    1. **What deleting leaves behind.** Cases: hidden, hidden with a
       restriction already there, hidden and deleted twice, and published.
       Two normal guards: the database's one-per-pair constraint, and a
       forced delete failure leaving neither a restriction nor a missing
       review. GREEN put `update_or_create` and the delete in one
       `transaction.atomic()` in `delete_by_author()`, copying the reason,
       moderator and time, and never the rating or comment.
    2. **A restriction blocks that product only.** GET and POST to create
       get 403 and nothing is saved. The product page shows the approved
       message instead of **Write a review**, and a second Delivered
       product can still be reviewed. GREEN added
       `ReviewRestriction.applies()`, checked in `can_create` and in a new
       `"restricted"` visitor state.
    3. **Clearing a restriction.** Ten cases: anonymous visitors to login,
       both customers 403, a POST without CSRF 403, a staff GET only
       confirming, a staff POST clearing it with the success message and
       the customer able to review again, and clearing twice giving the
       info message. RED used a skeleton built deliberately without the
       staff check, test-only until its GREEN, which added
       `StaffRequiredMixin` and `ReviewRestriction.clear()`: one targeted
       delete that reports whether it removed anything.
  - **Normal Phase 5 work (prompt 14):**
    - The Restrictions page: 25 a page, the PRD's columns, "Former staff
      member", an empty state, and a link from the Reviews list.
    - `ReviewRestrictionAdmin`: read-only, no Add, deletion allowed.
    - The product-delete warning: "This will also permanently delete N
      reviews. This can't be undone in the store."
    - The Phase 2 hidden-delete test updated to expect a restriction.
    - 18 normal tests: the page, other restrictions surviving a clear, a
      made-up id, a restricted customer who's ineligible or now staff, the
      cascades, the admin (including that admin deletion creates no
      restriction), and the warning.
    - The suite went from 743 to 778.
  - **Backup and migration (prompts 15–17):**
    - The first check found 5 `runserver` processes still running, so the
      agent made no copy and waited.
    - With the server stopped, it created
      `db.sqlite3.before-restrictions-backup`: 360,448 bytes, SHA-256
      matching the source (`918DED56…`), integrity ok, both reviews
      present, and only `0001` applied. Both older backups' hashes were
      unchanged.
    - `migrate --plan` listed only `reviews.0002_reviewrestriction`, and
      `migrate` applied it.
    - Afterwards: integrity ok, the restrictions table empty, both review
      rows identical to the backup field by field, and all three backups
      unchanged.
  - **Browser verification (prompt 18):** done by the developer, including
    the customer 403 check.
- **Deviations:**
  - Item 2 was a case inside Behavior 1 rather than its own cycle, because
    it already passed.
  - The migration file was created before Behavior 1's RED, with explicit
    approval. Applying it waited for the backup.
  - The agent never wrote out Phase 5 browser steps. After the migration
    it stopped as instructed, and the developer verified in the browser on
    their own.
- **Sideways:**
  - **Repeated prompts.** The same Phase 5 request arrived three times
    (prompts 6 and 7). The agent answered once and pointed back to it.
  - **A RED that wasn't an assertion.** Two Behavior 1 cases first failed
    with a `ValueError` from tuple unpacking. They were rewritten as an
    explicit count assertion before RED was reported.
  - **Two date tests that depended on the time of day.** During Behavior
    2's GREEN, two Phase 2 tests failed at 00:08 UTC. They built dates
    from the current UTC time, which displayed as the previous day in
    Chicago. They now use fixed noon-UTC datetimes; the assertions are
    unchanged.
  - **Small fixes:** one edit matched twice and was redone with more
    context. A new test compared the full message list across a GET and a
    POST that shared a session; it now checks that the message is present.
  - **A misleading migration check.** `showmigrations` against the
    in-memory database said nothing about the real one. The agent checked
    `db.sqlite3` read-only instead.

## 2026-10-18 — Product reviews Phase 4: back-office moderation (hide and restore)

### Prompts
The same agent session as the Phase 3 entry below, which records its own
prompts 1–12. Prompt text is verbatim. Prompts 1–3 staged, committed and
pushed Phase 3; they are recorded here because that entry was already
committed. Every prompt was pasted in, so `/implement` never ran as a
command; the agent followed it and `/tdd` directly.

1. I approve the proposed 8-file staging list for Product Reviews Phase 3.

   Stage only these exact paths:
   PROMPTS.md
   products/models.py
   products/views.py
   templates/products/catalog.html
   templates/reviews/partials/_reviews_section.html
   reviews/test_display.py
   reviews/test_pagination.py
   reviews/test_catalog.py

   Do not use git add . or git add -A.

   After staging, show git diff --cached --name-only, git diff --cached
   --stat, and git status --short. Verify there are exactly 8 staged files
   and no databases, backups, generated CSS, or unrelated files.

   Do not commit or push yet. Stop for my final review of the staged
   changes.

   Proposed future commit message: feat(reviews): add Phase 3 pagination
   and catalog ratings.
2. I give final approval to commit the 8 staged Product Reviews Phase 3
   files.

   Use this exact commit subject:
   feat(reviews): add Phase 3 pagination and catalog ratings

   You may include the repository's usual co-author trailer.

   Do not stage any additional files, amend previous commits, or include
   db.sqlite3, db.sqlite3.before-reviews-backup,
   db.sqlite3.before-wishlist-backup, or generated CSS.

   After committing, report the commit hash, git log -1 --oneline, and git
   status --short. Confirm the 8 approved files were committed and all
   database files were excluded.

   Do NOT push to GitHub yet. Stop for my separate push approval. Do not
   begin Phase 4.
3. I approve pushing the existing Phase 3 commit
   0cd0a12104513b0cd11a9455021d5bbdcfa92af5 to origin/main.

   First confirm HEAD is exactly that commit, fetch origin, and verify the
   push is a fast-forward with no unexpected remote changes. Then perform a
   normal git push origin main. Do not force-push, amend, stage, or commit
   anything else.

   After pushing, report the remote push result, confirm local main and
   origin/main point to the same commit, and show git status --short.

   Preserve db.sqlite3, db.sqlite3.before-reviews-backup, and
   db.sqlite3.before-wishlist-backup. Do not run seed, reset, or
   migrations.

   Stop after confirming the push. Do not begin Phase 4 until I give the
   next instruction.
4. Phase 3 has been successfully pushed to origin/main at commit
   0cd0a12104513b0cd11a9455021d5bbdcfa92af5. Begin ONLY Phase 4 of the
   approved Product Reviews PRD and implementation plan: staff review
   moderation.

   Follow the repository's .claude/skills/implement/SKILL.md and
   .claude/skills/tdd/SKILL.md, including all approval checkpoints.

   Before writing any tests or implementation code, review
   prd/product-reviews.md and plans/product-reviews.md, then propose up to
   three focused Phase 4 TDD behaviors for my approval. Cover staff-only
   access to the back-office Reviews section, review
   listing/filtering/pagination, and secure hide/restore moderation with a
   required reason where specified by the PRD. Explicitly identify access
   controls, POST/CSRF requirements, and published versus hidden
   visibility.

   Show the proposed RED/GREEN order and any open decisions, then STOP for
   my approval before writing code.

   Preserve db.sqlite3 and both existing database backups. Do not seed,
   reset, migrate or modify the development database. Do not alter the
   existing MindSync and SyncRest reviews. Use pytest's isolated test
   database for fixtures.

   Do not stage, commit, push, or begin Phase 5.
5. I approve all three proposed Phase 4 TDD behaviors, their order (1 → 2 →
   3), and all ten recommended open decisions.

   Begin Phase 4 Behavior 1 RED ONLY: back-office review moderation must be
   staff-only, with hide/restore actions POST-only and CSRF-protected.

   Create only the minimal routes/view skeleton necessary for an
   assertion-based RED test. Cover anonymous login redirects, authenticated
   customer and author 403 responses, GET requests to hide/restore
   returning 405, and POST requests without CSRF returning 403. Assert that
   denied requests never modify the review. Follow existing
   StaffRequiredMixin and back-office patterns.

   Demonstrate a genuine assertion failure for the missing security
   behavior, not a test collection/import error. Report the exact failing
   assertion and test command. Stop for my approval before implementing
   GREEN. Do not proceed to Behavior 2 or 3.

   The insecure RED skeleton must remain test-only development work: don't
   run it against the local development database or expose it through
   browser testing before GREEN.

   Preserve db.sqlite3, both backup files, and the existing MindSync and
   SyncRest reviews. Use only pytest's isolated database fixtures. Do not
   seed, reset, migrate, stage, commit, push, or begin Phase 5.
6. I approve Phase 4 Behavior 1 RED exactly as demonstrated: 12 assertion
   failures and 4 existing security checks passing.

   Proceed with GREEN for Behavior 1 ONLY.

   Apply the repository's existing StaffRequiredMixin access-control
   pattern to all four review moderation views: list, detail, hide, and
   restore. Ensure anonymous users redirect to login with the proper next
   parameter and authenticated nonstaff users (including review authors)
   receive 403. Keep hide and restore POST-only (GET must return 405 for
   staff) and protected by Django CSRF middleware (POST without token must
   return 403).

   Run all 16 Behavior 1 test cases, relevant reviews/back-office
   regression tests, the full pytest suite, and Ruff lint/format checks.
   Report exact results, including any failures or fixes, and STOP for my
   GREEN approval before beginning Behavior 2.

   Do not implement moderation state changes or listing/filtering behavior
   yet unless strictly required for Behavior 1 GREEN.

   Preserve db.sqlite3 and both backups, including the existing MindSync
   and SyncRest reviews. Use pytest's isolated database only. Do not seed,
   reset, migrate, stage, commit, push, or begin Phase 5.
7. I approve Phase 4 Behavior 1 GREEN. All 16 security cases pass, the full
   710-test suite passes, and Ruff is clean.

   Proceed with Phase 4 Behavior 2 RED ONLY: hiding a review requires a
   valid moderation reason and preserves an accurate audit trail.

   Write one focused parameterized TDD test using pytest's isolated
   database. Cover a valid 1–200-character reason trimmed before saving,
   changing a published review to HIDDEN, recording hidden_by and
   hidden_at, rejecting blank/whitespace-only and over-200-character
   reasons without changing the review, and making a second hide idempotent
   without overwriting the original moderator, timestamp or reason. Verify
   the appropriate detail-page error response or informational redirect
   for each case.

   Create only the minimal validation/action skeleton needed to demonstrate
   a genuine assertion-based RED failure. Keep all existing Behavior 1
   access controls, POST-only requirements, and CSRF protections in place.

   Run the new test and report the exact failing assertions. STOP for my
   approval before implementing GREEN, restoring reviews, or proceeding to
   Behavior 3.

   Do not modify, seed, reset, or migrate db.sqlite3 or either backup.
   Preserve my MindSync and SyncRest reviews. Do not stage, commit, push,
   or begin Phase 5.
8. I approve Phase 4 Behavior 2 RED: all seven parameterized cases fail on
   genuine assertions. I also approve the four exact message texts
   proposed in the RED test.

   Proceed with Behavior 2 GREEN ONLY.

   Implement the hide-review action for staff with a required, trimmed
   1–200-character reason. For a valid reason, atomically transition a
   PUBLISHED review to HIDDEN and record hidden_by, hidden_at, and
   hidden_reason. Redirect to the back-office review detail with the
   approved success message.

   For blank, whitespace-only, or over-200-character reasons, render the
   detail page with HTTP 200 and the exact approved validation message. Do
   not change the review or audit fields. For an already-hidden review,
   leave its original reason, moderator, and timestamp unchanged and show
   the exact approved informational message. Ensure repeated/concurrent
   hide requests cannot overwrite the original audit trail.

   Keep all Behavior 1 staff-only, POST-only, and CSRF protections. Do not
   implement restore behavior or public hidden-review presentation yet;
   those belong to subsequent work.

   Run all seven Behavior 2 cases, the 16 Behavior 1 security cases,
   relevant reviews/back-office regressions, the full pytest suite, and
   Ruff lint/format. Report exact results and STOP for GREEN approval
   before beginning Behavior 3.

   Preserve db.sqlite3, both backups, and my existing MindSync and SyncRest
   reviews. Use pytest's isolated database only. Do not seed, reset,
   migrate, stage, commit, push, or begin Phase 5.
9. I approve Phase 4 Behavior 2 GREEN. All seven moderation cases, the 16
   security cases, and the concurrent-hide regression pass. The full
   718-test suite passes, and Ruff is clean.

   Proceed with Phase 4 Behavior 3 RED ONLY: a hidden review disappears
   from all public review listings and rating summaries but remains
   visible to its author with the staff moderation reason.

   Write one focused parameterized TDD test using pytest's isolated
   database. Confirm that anonymous visitors and other customers cannot see
   the hidden review's comment or reason, that it is excluded from the
   product-detail published review list and published-only rating
   average/count, and that catalog and category cards also exclude it.
   Confirm the author still sees their own hidden review pinned under Your
   review, labeled 'Hidden by staff: <reason>' with the reason safely
   HTML-escaped, and with Delete but not Edit. Verify that a hidden review
   is not treated as a published review for public summaries. Include the
   expected after-restore public visibility in the test if it can be
   demonstrated without implementing restore yet; otherwise leave restore
   behavior for normal Phase 4 work.

   Use the existing published() queryset and current author-display
   behavior where appropriate. Write the minimum RED test, run it, and show
   genuine assertion failures. STOP for my RED approval before
   implementing GREEN.

   Preserve all Behavior 1 access checks, POST-only actions, CSRF
   protections, and Behavior 2 hide/audit functionality. Do not implement
   restore, listing/filtering/pagination, or the Reviews tab yet unless
   essential for RED.

   Do not modify, seed, reset, or migrate db.sqlite3 or either backup.
   Preserve my existing MindSync and SyncRest reviews. Do not stage,
   commit, push, or begin Phase 5.
10. I approve Phase 4 Behavior 3 RED exactly as demonstrated: 1 genuine
    assertion failure and 2 passing public-visibility cases.

    Proceed with Behavior 3 GREEN ONLY.

    Update the signed-in author's pinned Your review section so that when
    their review has HIDDEN status, it visibly displays 'Hidden by staff:
    <reason>' using Django's normal template escaping. Ensure any HTML in
    the reason renders as text, never markup or executable content.

    Preserve the current published-only behavior: anonymous visitors and
    other customers must not see the hidden review or reason, and hidden
    reviews must not contribute to product detail, catalog, or category
    rating counts and averages. The author must see their hidden review
    exactly once, with Delete available but Edit unavailable.

    Keep the implementation minimal and reuse the existing review
    partial/template wherever appropriate. Do not implement restore, staff
    listing/filtering/pagination, or the Reviews tab yet; those are
    remaining normal Phase 4 work.

    Run all three Behavior 3 cases, all 23 Behavior 1/2 cases, the
    concurrency regression, relevant reviews/products/back-office tests,
    the full pytest suite, and Ruff lint/format checks. Report exact
    results and STOP for my GREEN approval before continuing normal Phase 4
    work.

    Do not modify, seed, reset, or migrate db.sqlite3 or either backup.
    Preserve my MindSync and SyncRest reviews. Do not stage, commit, push,
    or begin Phase 5.
11. I approve Phase 4 Behavior 3 GREEN. All three cases pass, the full
    721-test suite passes, and Ruff is clean. All three Phase 4 TDD cycles
    are complete.

    Proceed with the remaining normal Phase 4 work according to
    prd/product-reviews.md and plans/product-reviews.md:

    1. Implement staff-only review listing with 25 reviews per page,
    newest-first ordering, a validated ?status= filter (PUBLISHED/HIDDEN),
    filter preservation across pagination, the required columns, an
    approximately 80-character excerpt, proper empty states, and 'Former
    staff member' when the hiding moderator no longer exists.
    2. Complete the back-office review detail page with the information and
    moderation controls required by the PRD. Include the Reviews navigation
    tab between Discount codes and Dashboard. Do not provide any staff
    delete action.
    3. Implement restore through a staff-only, POST-only, CSRF-protected
    action. Restoring must return the review to PUBLISHED and clear the
    hidden moderation fields as specified by the PRD. A second restore
    should make no changes and show an informational message. Verify that
    restored reviews appear again publicly and contribute to published-only
    ratings.
    4. Add focused normal regression tests for listing/filtering/pagination,
    invalid filter values, empty states, detail content, navigation
    placement, restore and restore-twice, and moderation permissions.
    Preserve the completed TDD behaviors and audit-trail protections.
    5. Verify any new template classes against the existing compiled CSS
    without rebuilding Tailwind or changing Windows security settings.

    Run the full pytest suite, Ruff lint and formatting, Django system
    checks, and makemigrations --check --dry-run. Report exact results and
    any deviations.

    Then STOP with precise browser verification steps. Do not hide or
    restore my real MindSync or SyncRest reviews automatically; use
    isolated pytest fixtures for all moderation testing. We can explicitly
    decide whether to do a temporary manual moderation test later.

    Do not modify, seed, reset, or migrate db.sqlite3 or either backup. Do
    not stage, commit, push, or begin Phase 5.
12. Phase 4 browser verification is complete. I verified the staff Reviews
    tab and detail page, Published/Hidden/invalid status filters, the
    anonymous login redirect, and that a signed-in customer receives 403
    Forbidden. I did not hide or restore either real review; those actions
    are verified through isolated pytest tests.

    Please complete the Phase 4 PROMPTS.md entry required by /implement.
    Document the three RED/GREEN TDD cycles, normal implementation work,
    moderation security decisions, browser verification, test results, and
    any deviations or troubleshooting.

    Then rerun the full pytest suite, Ruff lint/formatting, Django system
    checks, and makemigrations --check --dry-run. Show git status --short,
    the exact proposed files to stage, and a concise diff/stat.

    Do not stage, commit, or push yet. Explicitly exclude db.sqlite3,
    db.sqlite3.before-reviews-backup, db.sqlite3.before-wishlist-backup,
    generated CSS, and unrelated files. Preserve my existing MindSync and
    SyncRest reviews and all other local data.

    STOP for my approval of the staging list. Do not begin Phase 5.

### Summary
- **Outcome:** staff have a Reviews tab where they can find any review,
  hide it with a recorded reason, and restore it. Hidden reviews leave
  public view everywhere, but their authors still see them, marked.
  - **Phase 3 commit (prompts 1–3):** the 8 reviewed files were staged by
    path and committed as `0cd0a12`, a new commit on top of `807faf8`. It
    was pushed to `origin/main` as a fast-forward after a fresh fetch
    showed no unexpected remote changes.
  - **Planning (prompts 4–5):** the agent first read the Orders and
    Discount codes back office. It proposed three behaviors and ten
    decisions, and the developer approved all of them:
    - `?status=` takes the model's own values, and anything else shows all;
    - GET to an action gives 405;
    - actions redirect to the detail page;
    - an invalid reason re-shows the detail page with 200;
    - a bad `?page=` gives 404, like Orders;
    - staff see hidden reviews only in the back office;
    - a promoted author may moderate their own review;
    - a superuser without `is_staff` gets 403;
    - restoring doesn't depend on eligibility;
    - deleting a hidden review still just deletes it until Phase 5.

    Listing, filtering and paging were kept out of TDD, because the Orders
    pattern already settles them; they were built and tested normally.
  - **TDD (prompts 5–10):** three approved behaviors, each RED on an
    assertion, then GREEN with the full suite run:
    1. **Staff-only, POST-only and CSRF-protected.** One test with 16
       cases. Anonymous visitors are sent to login with `next`. Another
       customer and the review's own author get 403 on the list, detail,
       hide and restore. Staff get 405 for a GET to hide or restore, and
       403 for a POST without a CSRF token. No refused request changes the
       review. RED used a skeleton built deliberately **without** the staff
       check, run only by pytest, and 12 cases failed. The 405 and CSRF
       cases already passed, because they come from the POST-only `View`
       pattern and Django's middleware. GREEN added `StaffRequiredMixin` to
       all four views.
    2. **A required reason and an accurate record.** One test with seven
       cases: a trimmed reason, 1 and 200 characters, blank, whitespace,
       201 characters, and already hidden. The developer approved the four
       message texts. GREEN added `HideReviewForm`, plus `Review.hide()`:
       one conditional UPDATE (`filter(pk, status=PUBLISHED).update(...)`),
       so a second or concurrent hide can never overwrite the original
       moderator, time or reason. A model test with a stale copy proves the
       race.
    3. **Hidden from the public, visible to its author.** One test with
       three cases (anonymous, another customer, the author). The review is
       hidden through the real staff action, with the reason
       `<b>Spam</b> & links`. `published()` already kept it out of the
       product list, the summaries and the catalog and category cards, so
       only the author case failed. GREEN added an auto-escaped
       "Hidden by staff: <reason>" alert to the pinned "Your review" area.
  - **Normal Phase 4 work (prompt 11):**
    - `Review.restore()`, the same conditional-UPDATE design as `hide()`.
    - The restore view, with a success message and an info message for
      restoring twice.
    - The list: 25 a page, newest first, the validated filter kept across
      pages, the required columns, the 80-character excerpt, "Former staff
      member", and both empty states.
    - The detail page: the full escaped comment, the dates, the moderation
      record, and Hide or Restore. There's no delete anywhere.
    - The Reviews tab between Discount codes and Dashboard, and a shared
      `_moderation_status.html` partial.
    - 22 normal tests, including a stale-restore model test.
    - The suite went from 694 to 743.
  - **Browser verification (prompt 12):** done by the developer as staff, a
    customer and a signed-out visitor: the tab, the detail page, the
    Published, Hidden and invalid filters, the login redirect, and the 403.
    Neither real review was hidden or restored; those actions were tested
    only in pytest's isolated database.
- **Deviations:**
  - The insecure Behavior 1 skeleton existed only in the working tree until
    its GREEN, as the developer required. It was never served from
    `db.sqlite3` or opened in a browser.
  - Actually hiding and restoring, the author's "Hidden by staff" label,
    "Former staff member", and paging past 25 were tested rather than
    checked in the browser, to protect the developer's real reviews. A
    temporary manual moderation test was offered for later.
- **Sideways:**
  - **Two drafts of the Behavior 1 test.** The first draft was two test
    functions. The agent merged them into one test with an explicit case
    list, to keep `/tdd`'s rule of one test per behavior.
  - **A test sent a body with its GETs.** Behavior 1's first GREEN run had
    14 of 16 passing. The test sent `{"reason": "Spam"}` with every
    request, and on a GET that became the query string, so the login
    `next` included it. That was a mechanical setup fix, sending the reason
    only with POSTs; no assertion changed.
  - **Failed shell commands.** One combined check command failed to parse,
    because PowerShell broke on the embedded bash quoting; it was rerun
    split. A Bash heredoc holding the normal tests also failed to parse, so
    nothing was appended. The agent confirmed the file was unchanged, then
    wrote the tests with the Write tool and appended them.
  - **Missing CSS classes.** `mb-2` and `btn-warning` aren't in the
    compiled CSS. They were replaced with `mb-4` and `btn-error`. The CSS
    check's other "MISSING" lines were template code, and a direct check
    confirmed the two `lg:` classes are present.

## 2026-10-18 — Product reviews Phase 3: review pagination and catalog ratings

### Prompts
The same agent session as the Phase 2 entry below, which records its own
prompts 1–13. Prompt text is verbatim. Prompts 1–3 staged, committed and
pushed Phase 2; they are recorded here because that entry was already
committed. Every prompt was pasted in, including prompt 4, so `/implement`
never ran as a command; the agent followed its steps directly.

1. I approve the proposed 13-file staging list for Product Reviews Phase 2.

   Stage only these exact paths:
   PROMPTS.md
   products/views.py
   reviews/forms.py
   reviews/models.py
   reviews/urls.py
   reviews/views.py
   reviews/test_display.py
   reviews/test_eligibility.py
   reviews/test_views.py
   templates/reviews/partials/_review.html
   templates/reviews/partials/_reviews_section.html
   templates/reviews/review_form.html
   templates/reviews/review_confirm_delete.html

   Do not use git add . or git add -A.

   After staging, show git diff --cached --name-only, git diff --cached
   --stat, and git status --short. Verify there are exactly 13 staged files
   and no database, backup, compiled CSS, or unrelated files.

   Do not commit or push yet. Stop for my final review of the staged
   changes.

   Proposed future commit message: feat(reviews): add Phase 2 review
   editing and deletion.
2. I give final approval to commit the 13 staged Product Reviews Phase 2
   files.

   Use this exact commit subject:
   feat(reviews): add Phase 2 review editing and deletion

   You may include the repository's usual co-author trailer.

   Do not stage additional files, amend previous commits, or include
   db.sqlite3, db.sqlite3.before-reviews-backup,
   db.sqlite3.before-wishlist-backup, or generated CSS.

   After committing, show the commit hash, git log -1 --oneline, and git
   status --short. Confirm that the 13 approved files were committed and
   the database files remain outside this commit.

   Do NOT push to GitHub yet. Stop for my separate push approval. Do not
   begin Phase 3.
3. I approve pushing the existing Phase 2 commit
   807faf81a53aea9766234d1a7b2590533db542e9 to origin/main.

   First verify HEAD is that commit, fetch origin, and confirm the push is a
   fast-forward with no unexpected remote changes. Then perform a normal
   git push origin main. Do not force-push, amend, stage, or commit
   anything else.

   Afterward, report the push result, confirm local main and origin/main
   point to the same commit, and show git status --short.

   Preserve db.sqlite3, db.sqlite3.before-reviews-backup, and
   db.sqlite3.before-wishlist-backup exactly as they are. Do not run seed,
   reset, or migrations.

   Stop after confirming the push. Do not begin Phase 3 until I give the
   next instruction.
4. Implement only Phase 3 of the approved Product Reviews PRD and plan,
   following /implement and every /tdd approval checkpoint.

   Before writing tests or implementation code, propose up to three Phase 3
   TDD behaviors for my approval. Include 10-reviews-per-page pagination
   with 11+ reviews created only in an isolated test database; graceful
   handling of invalid and out-of-range page parameters; and correct
   published-only catalog rating/count annotations under search and
   filters, with an appropriate query-count regression.

   Preserve the existing MindSync review and all development database
   records. Do not seed, reset, migrate, or alter db.sqlite3 or either
   backup. Do not create 11+ reviews in my development database; use pytest
   fixtures only.

   Do not stage, commit, push, or begin Phase 4. Stop for approval before
   each RED and GREEN step, and before browser verification.
5. I approve all three proposed Phase 3 TDD behaviors and their order.

   Begin Behavior 1 RED only: 10 published reviews per page, newest first,
   with the 11th review appearing on page 2.

   Build the minimum pagination skeleton normally, then write and run the
   RED test. Use 11 separate eligible customers with qualifying Delivered
   orders in pytest's isolated test database only. Verify page 1 shows
   exactly the 10 newest reviews, page 2 shows only the oldest review, and
   that a signed-in author's pinned review is not duplicated in the
   paginated public list.

   Preserve ordering by created_at descending with pk as the tie-breaker,
   and use the ?reviews=2#reviews URL convention.

   Stop after demonstrating the expected RED assertion failure. Do not
   implement GREEN until I approve it.

   Do not seed, migrate, reset, or modify db.sqlite3 or either database
   backup. Do not stage, commit, push, or begin another behavior or phase.
6. I approve the Phase 3 Behavior 1 RED test, including both anonymous and
   signed-in author cases.

   Proceed with GREEN for Behavior 1 only. Implement server-side pagination
   of the published public review list at exactly 10 reviews per page,
   ordered by -created_at and -pk. Keep the signed-in author's own review
   pinned separately on every page and excluded from the paginated public
   queryset, with no duplication.

   Use the reviews query parameter without interfering with other
   product-page behavior. Preserve the one-decimal published-only rating
   summary, which must include the author's published review even when
   excluded from the public list.

   Run both Behavior 1 cases, the reviews app regression tests, the
   complete suite, and Ruff lint/format checks. Report exact results and
   STOP for my GREEN approval before Behavior 2.

   Leave invalid page parameter handling for Behavior 2's TDD cycle and
   Newer/Older navigation links for the remaining normal Phase 3 work,
   unless strictly necessary for the minimum GREEN implementation.

   Do not modify, seed, reset or migrate my development database or either
   backup. Do not stage, commit, push, or begin Phase 4.
7. I approve Phase 3 Behavior 1 GREEN. The full 679-test suite passes, and
   Ruff is clean.

   Proceed with Behavior 2 RED only: invalid and out-of-range review
   pagination parameters must be handled gracefully.

   Using the existing isolated 11-review test fixture, write and run an
   assertion-based RED test verifying that ?reviews=abc returns HTTP 200
   with page 1 (10 newest reviews), while ?reviews=99 returns HTTP 200 with
   the last page (the oldest review). Also cover zero or negative page
   numbers if appropriate to the approved PRD.

   Do not implement GREEN until I approve the RED results. Keep all tests
   in the isolated pytest database.

   Do not modify, migrate, seed, or reset db.sqlite3 or either backup. Do
   not stage, commit, push, or begin Behavior 3 or Phase 4.
8. I approve Phase 3 Behavior 2 RED and all five test cases exactly as
   written.

   I confirm the pagination behavior: non-numeric or empty reviews
   parameters display page 1; out-of-range numbers, including 0 and
   negatives, display the last page. All cases must return HTTP 200.

   Proceed with GREEN for Behavior 2 only. Use Django's
   Paginator.get_page() if appropriate, preserving the
   10-reviews-per-page behavior, newest-first ordering, and separately
   pinned author review.

   Run all five Behavior 2 cases, the Behavior 1 pagination regressions,
   all reviews tests, the full regression suite, and Ruff lint/format
   checks. Report exact results and STOP for my GREEN approval before
   starting Behavior 3.

   Do not modify, seed, migrate, or reset db.sqlite3 or either backup. Do
   not stage, commit, push, or begin Phase 4.
9. I approve Phase 3 Behavior 2 GREEN. All 684 tests pass, and Ruff is
   clean.

   Proceed with Behavior 3 RED only: product catalog cards must display
   accurate published-only review averages and counts under combined
   search and tag/category filters, without N+1 database queries.

   Build the minimum normal skeleton for ProductQuerySet.with_ratings() and
   the catalog card rating summary if needed. Then write and run an
   assertion-based RED test using isolated pytest fixtures with multiple
   products, published and hidden reviews, and products sharing tags.
   Verify that filters and search return the correct products without
   duplicating review counts, that hidden reviews do not affect averages,
   that zero-review products show the empty state, and that the number of
   database queries does not increase proportionally with the number of
   cards.

   Keep the query-count assertion practical and deterministic, measuring
   the same catalog request shape for smaller and larger result sets. Do
   not assume a specific total query count without inspecting the existing
   view's expected queries.

   Stop after demonstrating the expected RED failure. Do not implement
   GREEN until I approve it.

   Do not modify, seed, reset, or migrate db.sqlite3 or either backup. Do
   not stage, commit, push, or begin Phase 4.
10. I approve the Phase 3 Behavior 3 RED test exactly as written, including
    the catalog and category scenarios and the measured query-count
    comparison.

    Proceed with GREEN for Behavior 3 only.

    Implement ProductQuerySet.with_ratings() with efficient database-side
    annotations for published-only review average and count. Make sure
    joining or filtering by multiple tags cannot inflate the counts or
    averages, and preserve correct product search, category, and tag
    filtering. Keep zero-review cards showing No reviews yet. Do not make
    one rating query per product card.

    Run the approved catalog test, query-count regression, relevant
    reviews/products tests, the full regression suite, and Ruff lint/format
    checks. Report the exact results and STOP for my GREEN approval before
    continuing the remaining normal Phase 3 work.

    Do not modify, seed, migrate, or reset db.sqlite3 or either backup. Do
    not stage, commit, push, or begin Phase 4.
11. I approve Phase 3 Behavior 3 GREEN. All 685 tests pass, and Ruff is
    clean. All three Phase 3 TDD cycles are complete.

    Proceed with the remaining normal Phase 3 work according to
    prd/product-reviews.md and plans/product-reviews.md:

    1. Implement accessible Newer/Older review pagination links pointing to
    ?reviews=N#reviews. Show only appropriate links at the beginning/end of
    the pagination, and preserve the separately pinned Your review section.
    2. Verify that catalog and category cards display published-only
    ratings for unavailable products too, and show No reviews yet for
    products with no published reviews.
    3. Add focused tests for navigation links, pagination boundaries,
    author pinning, unavailable products, and any relevant filter/query
    regressions.
    4. Check that all classes used in the new templates exist in the
    current compiled CSS without rebuilding Tailwind or changing Windows
    security settings.

    Run the full regression suite, Ruff lint, Ruff format, Django system
    checks, and makemigrations --check --dry-run. Fix any failures.

    Then STOP and give me Phase 3 browser verification instructions. The
    existing development database has only my MindSync review, so do not
    create 11+ reviews there. Pagination with 11+ reviews must be verified
    using isolated pytest fixtures only.

    Do not modify, seed, reset, or migrate db.sqlite3 or either database
    backup. Do not stage, commit, push, or begin Phase 4.
12. Phase 3 browser verification is complete. I confirmed MindSync and
    SyncRest catalog ratings, MindSync search results, both bestseller and
    implant tag filters, and invalid review page parameters (?reviews=abc,
    ?reviews=99, ?reviews=-1) all work correctly. The 11-review and
    21-review pagination cases are covered by isolated automated tests.

    Please complete the Phase 3 PROMPTS.md entry required by /implement.
    Document the three TDD cycles, implementation decisions, browser
    verification, test results, and any deviations or troubleshooting.

    Then rerun the full pytest suite, Ruff lint and formatting, Django
    system checks, and makemigrations --check --dry-run. Show git status
    --short, the exact proposed files to stage, and a concise diff/stat.

    Do not stage, commit, or push yet. Explicitly exclude db.sqlite3,
    db.sqlite3.before-reviews-backup, db.sqlite3.before-wishlist-backup,
    and generated CSS. Preserve my existing MindSync and SyncRest reviews
    and all other local data.

    Stop for my approval of the staging list. Do not start Phase 4.

### Summary
- **Outcome:** product pages show reviews 10 at a time with Newer and Older
  links, and catalog and category cards show each product's rating.
  - **Phase 2 commit (prompts 1–3):** the 13 reviewed files were staged by
    path and committed as `807faf8`, a new commit on top of `47160b0`. It
    was pushed to `origin/main` as a fast-forward after a fresh fetch
    showed no unexpected remote changes.
  - **TDD (prompts 5–10):** three approved behaviors, each RED on an
    assertion, then GREEN with the full suite run:
    1. **10 reviews a page, newest first, the oldest on page 2.** A fixture
       builds 11 regular customers, each with their own Delivered order and
       one published review, in the test database only. Viewed anonymously
       and as an author whose own review is the newest of all. GREEN paged
       the public list with Django's `Paginator` on `?reviews=N`, ordered
       `-created_at, -pk`, with the author's review excluded before paging.
       A regression test confirms the rating summary still counts that
       review.
    2. **Bad page numbers never error.** `abc` and an empty value go to
       page 1; `99`, `0` and `-1` go to the last page, all with 200. The
       agent asked about 0 and negatives before GREEN. The PRD's "an
       out-of-range page shows the last page" covers them, and the
       developer confirmed it. GREEN was one change: `Paginator.page()` to
       `get_page()`.
    3. **Catalog and category cards show published-only ratings under
       search and tag filters, with a fixed query count.** Halo One has two
       tags and a hidden review. Halo Three has no reviews, and Quiet Box is
       excluded by the search. The same filtered request is measured at 3
       and 9 cards. GREEN gave `ProductQuerySet.with_ratings()` two
       correlated subqueries over published reviews, so no tag or search
       join can repeat rows, and `Coalesce(…, 0)` for products without
       reviews. `Review` is imported inside the method, because
       `reviews.models` already imports `products.models`.
  - **Normal Phase 3 work (prompt 11):**
    - A `<nav aria-label="Review pages">`: "← Newer reviews" (`rel="prev"`)
      only when there's a newer page, "Page X of Y", and "Older reviews →"
      (`rel="next"`) only when there's an older one. Both link to
      `?reviews=N#reviews`, and the nav is hidden when one page is enough.
    - Tests for each link boundary: a 21-review middle page, a fallback
      page's links, no links for 10 reviews, the author pinned above the
      links on both pages, an unavailable product's rating on catalog and
      category pages, an all-hidden product showing "No reviews yet", and
      ratings on the catalog's own `?page=2`.
    - Every class used by the new templates exists in the compiled CSS.
      Tailwind was not rebuilt.
    - 18 new tests; the suite went from 676 to 694.
  - **Browser verification (prompt 12):** done by the developer:
    - MindSync and SyncRest ratings on the catalog;
    - a MindSync search;
    - the bestseller and implant tag filters;
    - `?reviews=abc`, `?reviews=99` and `?reviews=-1`.

    Pagination with 11 and 21 reviews was verified only in pytest's
    isolated database.
- **Deviations:**
  - The browser couldn't show page links or an unavailable product with a
    rating without adding reviews to the developer's data, so tests cover
    both.
  - `/implement` was followed manually; every prompt was pasted.
- **Sideways:**
  - **A temporary 500 between Behaviors 1 and 2.** Behavior 1's
    `Paginator.page()` turned `?reviews=abc` and `?reviews=99` from ignored
    into a 500, because Behavior 2 was to define the fix. The agent
    disclosed this at Behavior 1's GREEN. `get_page()` closed it at
    Behavior 2.
  - **Measuring before trusting the query count.** The developer asked for
    the existing view's queries to be inspected first. The agent wrote a
    throwaway probe test, ran it once (5 queries at both 3 and 9 cards:
    product count, categories, tags, products, tag prefetch), and deleted
    it before reporting RED.
  - **An unfinished test.** The first draft of the catalog second-page
    test never checked a rating and had a stray comment. It was rewritten
    before any run.
  - **Small fixes:** an `HTTPStatus` import landed above `datetime` and was
    reordered for Ruff; a `.format()` call became an f-string.
  - **A noisy CSS check.** It reported false "MISSING" classes: template
    code inside `catalog.html`'s existing class attributes, and variant
    classes such as `hover:shadow-xl` that its pattern didn't escape. A
    plain-text search confirmed every one exists.
  - **The developer's note was off by one review.** Prompt 11 said the
    database held only the MindSync review. A read-only check found a
    published SyncRest review too, left from the Phase 2 browser check.
    The browser steps were written for both.

## 2026-10-18 — Product reviews Phase 2: edit and delete your own review

### Prompts
The same agent session as the Phase 1 entry below, which records prompts
1–17. Prompt text is verbatim. Prompts 1–3 staged, committed and pushed
Phase 1; they are recorded here because that entry was already committed.
Prompt 4 was typed as a slash command; the rest were pasted in. Prompt 8
was sent twice word for word, so the second copy (prompt 9) is described
rather than repeated.

1. I approve the proposed 28-file staging list for Product Reviews Phase 1.

   Stage only those exact approved source, template, test, PRD, plan, and
   PROMPTS.md paths. Do not use git add . or git add -A.

   After staging, show me git diff --cached --name-only, git diff --cached
   --stat, and git status --short. Verify that the three database files are
   NOT staged: db.sqlite3, db.sqlite3.before-wishlist-backup, and
   db.sqlite3.before-reviews-backup. Also confirm no unrelated files or
   generated CSS assets are staged.

   Do not commit or push yet. Stop for my final review of the staged
   changes. The proposed eventual commit message is: feat(reviews):
   implement Phase 1 product reviews and ratings.
2. I give final approval to commit the 28 staged Product Reviews Phase 1
   files.

   Use the commit message:
   feat(reviews): implement Phase 1 product reviews and ratings

   You may include the repository's usual co-author trailer.

   Do not stage any additional files. Do not include db.sqlite3,
   db.sqlite3.before-wishlist-backup, db.sqlite3.before-reviews-backup, or
   generated CSS.

   After committing, report the commit hash, git log -1 --oneline, and git
   status --short. Confirm the three database files remain outside Git.

   Do NOT push to GitHub yet. Stop for my separate push approval. Do not
   begin Phase 2.
3. I approve pushing the existing Phase 1 commit 47160b0 to origin/main.

   First confirm that HEAD is still 47160b0 and that the remote branch can
   be fast-forwarded. Then push only the existing commit to origin/main
   using a normal git push. Do not force-push, amend the commit, or stage
   any additional files.

   After pushing, report the remote push result, git status --short, and
   whether main is synchronized with origin/main.

   Leave db.sqlite3 and both database backups untouched. Do not run seed or
   start Phase 2 yet.
4. /implement @prd/product-reviews.md @plans/product-reviews.md implement
   phase 2
5. I approve all three proposed Phase 2 TDD behaviors and their order.

   Begin Behavior 1 only. Build the minimal edit-view skeleton and stub
   eligibility helpers as needed, then write and run the RED test for
   edited_at changing only when the review rating or comment actually
   changes, while created_at remains unchanged. Cover both unchanged
   submissions and real changes.

   Stop after showing the expected RED assertion failure. Do not implement
   GREEN until I approve it.

   Preserve all existing database records, including my MindSync review,
   and both backups. Use isolated test databases only. Do not seed, reset,
   migrate my development database, stage, commit, push, or begin another
   behavior or phase.
6. I approve the Phase 2 Behavior 1 RED test and all four cases exactly as
   written.

   Proceed with GREEN for Behavior 1 only. Set edited_at only when the
   stored rating or normalized/trimmed comment genuinely changes. Preserve
   created_at and existing review ordering. Ensure a review previously
   edited does not receive a new edited_at timestamp for an unchanged
   submission.

   Run the Behavior 1 tests, relevant regression tests, the full suite, and
   Ruff lint/format checks. Report exact results and stop for my GREEN
   approval before starting Behavior 2.

   Do not implement Behavior 2 or 3 yet. Do not seed, migrate, reset,
   modify my development database, stage, commit, push, or touch either
   database backup.
7. I approve Phase 2 Behavior 1 GREEN. All 639 tests pass, and Ruff is
   clean.

   Proceed with Behavior 2 RED only: an original review author who is
   subsequently promoted to staff must still be able to delete their own
   review, but must not be allowed to edit it.

   Build the minimal delete-route and delete-view skeleton normally,
   keeping deletion behind a GET confirmation page and POST-only
   destructive action. Then write and run the RED test against both edit
   and delete endpoints. Confirm the staff author receives 403 when
   attempting to edit, but can access their own delete confirmation and
   delete via POST. Include an assertion that GET does not delete the
   review.

   Keep the distinction between can_edit and can_delete, and preserve the
   signed-in authorship rule. Stop after the expected RED assertion
   failure, before implementing GREEN.

   Do not begin Behavior 3, seed, reset, migrate or change db.sqlite3,
   touch either backup, stage, commit, or push.
8. I approve the Phase 2 Behavior 2 RED test exactly as written.

   Proceed with GREEN for Behavior 2 only.

   Implement Review.can_edit(user) so editing requires all three
   conditions: (1) the user is the review's original author, (2) the user
   is currently a regular non-staff, non-superuser customer, and (3) the
   user currently has a Delivered OrderItem for that exact product. Do not
   use can_create for this check, because an existing review intentionally
   makes can_create false.

   Keep Review.can_delete(user) based solely on authenticated authorship,
   even if the author becomes staff or loses Delivered-order eligibility.
   Preserve the GET confirmation and POST-only deletion rules.

   Run the approved Behavior 2 test and add focused normal regression tests
   for loss of Delivered eligibility and ownership as appropriate. Run the
   reviews tests, full regression suite, Ruff lint and formatting. Report
   exact results and STOP for my GREEN approval before Behavior 3.

   Do not modify my development database or backups, migrate, seed, stage,
   commit, push, or begin Phase 3.
9. *(Prompt 8 sent again, word for word, while the full suite was still
   running.)*
10. I approve Phase 2 Behavior 2 GREEN. All 648 tests pass and Ruff is
    clean.

    Before Behavior 3, add the one missing PRD safeguard as normal
    regression work: Review.can_edit must also require status ==
    Review.Status.PUBLISHED. Add a focused test showing an eligible author
    of a hidden review cannot edit it but can still access their delete
    confirmation. Do not implement ReviewRestriction yet; that belongs to
    Phase 5. Run relevant tests.

    Then proceed with Behavior 3 RED only: a signed-in user who does not own
    a review for the requested product must receive HTTP 404 on both edit
    and delete endpoints. Ensure the test covers the case where another
    user's review exists for the product, without revealing or modifying
    that review. Build only necessary skeleton changes and demonstrate the
    expected RED assertion failure.

    Stop for my RED approval before implementing GREEN for Behavior 3. Do
    not begin remaining normal Phase 2 work yet.

    Do not migrate, seed, reset or modify my development database or either
    backup. Do not stage, commit, or push.
11. I approve the Phase 2 Behavior 3 RED test, including all four GET/POST
    cases, exactly as written.

    Proceed with GREEN for Behavior 3 only.

    Make both edit and delete endpoints return HTTP 404 when an
    authenticated visitor has no review of their own for the requested
    product, even if another customer has reviewed it. Preserve the
    existing HTTP 403 rule when the visitor owns a review but is not
    authorized to edit it. Anonymous visitors must still be redirected to
    login rather than receiving 404.

    Ensure the other customer's review and comment are never exposed or
    modified. Keep delete confirmation GET read-only and deletion POST-only.

    Run all four Behavior 3 cases, relevant authorization regressions, the
    complete test suite, and Ruff lint/format checks. Report exact results
    and stop for my GREEN approval before continuing the remaining Phase 2
    work.

    Do not modify my development database or backups, migrate, seed, stage,
    commit, push, or start Phase 3.
12. I approve Phase 2 Behavior 3 GREEN. All 657 tests pass, and Ruff is
    clean. All three Phase 2 TDD cycles are complete.

    Proceed with the remaining normal Phase 2 work according to
    prd/product-reviews.md and plans/product-reviews.md:
    - Add Edit and Delete controls in the pinned Your review section. Show
    Edit only when Review.can_edit allows it; allow Delete for the author
    even when editing is forbidden.
    - Display the Edited date only when edited_at is set, preserving the
    original posted date.
    - Complete and test the delete confirmation and POST-only deletion flow.
    - Test that deleting a published review allows the customer to write a
    fresh review if still eligible.
    - Add the outstanding order-status regression and any necessary
    authorization, template, date, and form tests.

    Important: Phase 5 will handle restrictions for hidden-review deletion.
    Do not implement that branch or ReviewRestriction now.

    Run the full regression suite, Ruff lint, Ruff format, Django system and
    migration checks. Fix any failures.

    Then STOP and give me precise Phase 2 browser verification instructions
    using my existing development database and customer account. Do not
    modify or seed my database directly, apply migrations, stage, commit,
    push, or begin Phase 3. Preserve both database backups and the existing
    MindSync review.
13. Phase 2 browser verification is complete. I confirmed editing a
    SyncRest review, unchanged saves not setting Edited, real changes
    setting Edited, canceling deletion preserving the review, POST deletion
    working, and successfully creating a new review after deletion. Both
    edit and delete of a nonexistent own DreamWeaver review return 404.
    Anonymous edit and delete URLs redirect to login. My original MindSync
    review was preserved.

    Please complete the Phase 2 PROMPTS.md entry required by /implement,
    documenting the TDD cycles, decisions, verification and any deviations.

    Then run final full pytest, Ruff lint/format, Django system checks, and
    makemigrations --check --dry-run. Show git status --short and the exact
    proposed Phase 2 files to stage, including a concise diff/stat.

    Do not stage, commit, or push yet. Do not modify, seed, reset, or
    migrate my db.sqlite3, and do not touch
    db.sqlite3.before-wishlist-backup or db.sqlite3.before-reviews-backup.
    Exclude all three database files and generated CSS from the proposed
    staging list.

    Stop for my approval of the staging list. Do not begin Phase 3.

### Summary
- **Outcome:** an author can edit their own review while still eligible,
  and can always delete it after a confirmation step.
  - **Phase 1 commit (prompts 1–3):** the 28 reviewed files were staged by
    path. The commit is `47160b0`, pushed to `origin/main` as a
    fast-forward from `f067450`. The agent corrected one point: the
    developer asked it to confirm all three database files "remain outside
    Git", but `db.sqlite3` has been tracked since before this session. It
    was left out of the commit, and its local changes stay uncommitted.
  - **TDD (prompts 5–11):** three approved behaviors, each RED on an
    assertion, then GREEN with the full suite run:
    1. **`edited_at` only on a real change.** Four cases: unchanged, only
       whitespace, a new rating, a new comment. `created_at` never moves.
       `ReviewForm.save` sets `edited_at` only when `has_changed()`
       compares the stored values with the cleaned submission and finds
       a difference, and only for an existing review.
    2. **A promoted author can delete but not edit.** `can_edit` needs the
       signed-in author, a regular customer, and a Delivered order for this
       exact product (`is_by`, `is_regular_customer`, `has_received`).
       `can_create` now shares those two helpers. `can_delete` is
       authorship only.
    3. **404 with no review of your own** on edit and delete, GET and POST,
       even when another customer has reviewed the product. Their review is
       never shown or changed. A shared `OwnReviewMixin` gives a fixed
       order: anonymous → login, no review of yours → 404, your review but
       not allowed → 403.
  - **Normal Phase 2 work (prompts 10 and 12):**
    - `can_edit` also requires a published review, the PRD rule the agent
      flagged at Behavior 2's GREEN.
    - Edit and Delete controls in "Your review": Edit only while allowed,
      Delete always.
    - "Posted … · Edited …" on the pinned and public reviews.
    - The delete confirmation page (POST form with CSRF, **Keep it**
      link), and `delete_by_author()` for published reviews.
    - Tests: losing Delivered status, a superuser author, other users,
      anonymous edit and delete, the hidden-author safeguard, the edit
      form's starting values and errors, list position, the delete flow, a
      fresh review after deleting, and an order-status change leaving the
      review public.
    - 42 new tests; the suite went from 634 to 676.
  - **Browser verification (prompt 13):** done by the developer as
    `customer` on a temporary SyncRest review, plus the DreamWeaver 404s
    and the anonymous redirects. The MindSync review was preserved.
- **Deviations:**
  - The published-status rule for editing was added before Behavior 3 at
    the developer's request (prompt 10). The Behavior 2 instruction had
    listed only three conditions.
  - Deleting a hidden review still just deletes it. The repost restriction
    is left for Phase 5, as instructed, and a test records that.
  - The 403 case for an author who can't edit was not checked in the
    browser, because reaching it would mean changing the developer's data.
    View and page tests cover it.
- **Sideways:**
  - **A stray block in `forms.py`.** The first Behavior 1 edit left a
    meaningless `_unused = {…}` block at the bottom of `ReviewForm`. The
    agent saw it, removed it before running any test, and disclosed it.
  - **A duplicate prompt.** Prompt 8 arrived a second time while the full
    suite was still running. The agent reported the finished work instead
    of redoing it.
  - **A failed check command.** A combined Ruff, Django and CSS-class
    check failed to parse, because PowerShell broke on the embedded bash
    quoting; none of it ran. It was rerun split into PowerShell and Bash
    calls.
  - **A brittle assertion.** A test matched the checked radio's exact
    template whitespace. It was loosened to a regex before the final run.

## 2026-10-18 — Product reviews: PRD finalized, six-phase plan, Phase 1 (write and display reviews)

### Prompts
One agent session, which resumed the product-reviews homework after a break.
Prompt text is verbatim, typos included. Most prompts were pasted in, so
they reached the agent as plain text. The exceptions are prompt 6, typed as
a slash command, and prompt 7, typed directly. Prompt 11 is described
rather than reproduced: it was a copy of the agent's own previous update.

1. We're resuming Lesson 10 Product Reviews after a break. First check
   whether prd/product-reviews.md or plans/product-reviews.md already exist
   and what work was completed. Read CLAUDE.md and any existing Product
   Reviews files. Do not restart the 19-question interview.

   Our next task is to finalize the Product Reviews PRD. We approved using
   /backoffice/ URLs, a separate reviews Django app, the four proposed
   defaults, and leaving TDD phase selection for the implementation plan. We
   also requested confirmation that seeded Delivered orders support more
   than 10 eligible published reviews for one product, and POST-only
   restriction clearing after a GET confirmation page.

   Report the current status and what remains to be done before editing
   anything. Do not implement code, run seed, modify or reset db.sqlite3, or
   touch db.sqlite3.before-wishlist-backup.
2. Thank you for identifying the conflict. Here are my final decisions.

   The four previously approved defaults are:
   1. Set edited_at only when the rating or comment actually changes.
   2. Make moderation fields read-only in Django admin.
   3. Return HTTP 404 for edit/delete pages when the signed-in user has no
   review to act on.
   4. If a ReviewRestriction already exists, update it rather than creating
   a duplicate.

   For the pagination conflict, keep 10 reviews per page and preserve all
   existing seeded users, orders, and dashboard metrics. Remove the
   requirement that the demo seed itself produce more than 10 reviews for
   one product. Keep the seed realistic: reviews only from customers with
   qualifying Delivered orders. State the actual maximum of five eligible
   reviewers per product found in your simulation.

   Test pagination using isolated pytest fixtures that create at least 11
   eligible reviewers with Delivered orders for the same product. Do not
   modify the development database for this.

   Please revise prd/product-reviews.md to resolve the constraint and
   confirm the four defaults. Preserve all other approved requirements. Show
   me a concise diff/summary of the changes and then draft the phased
   implementation plan for review before saving it.

   Do not write application code, make migrations, run seed against
   db.sqlite3, or touch my database backup.
3. I approve the revised Product Reviews PRD and the proposed SIX-PHASE
   implementation plan.

   Keep Phases 4 and 5 separate. For Phase 6, I approve isolated automated
   verification instead of running the destructive seed command against my
   personal development database.

   Before the first local migration, stop and help me create
   db.sqlite3.before-reviews-backup. Never modify, delete, or overwrite
   db.sqlite3.before-wishlist-backup.

   Ensure Phase 1 establishes the Review model and published-only query
   behavior needed for later moderation, without unnecessary changes to
   existing tables.

   Save the plan to plans/product-reviews.md, then confirm both the PRD and
   plan are saved. Show git status and the six phase headings.

   Do not implement Phase 1 yet, make migrations, run seed, or touch my
   development database. Stop after saving the plan and wait for my next
   instruction.
4. /implement @prd/product-reviews.md @plans/product-reviews.md implement
   phase 1

   Implement only Phase 1 and follow every /tdd approval checkpoint. Before
   any migration is applied to my development database, stop and help me
   create db.sqlite3.before-reviews-backup without overwriting any existing
   backup.

   You may create migration files and run automated tests in their isolated
   test database. Do not run seed against db.sqlite3. Do not touch
   db.sqlite3.before-wishlist-backup.

   After automated checks, give me browser verification instructions and
   stop for approval before committing or moving to Phase 2.
5. I approve all three proposed Phase 1 TDD behaviors:
   1. Delivered-order eligibility for the exact product, excluding other
   statuses and staff/admin.
   2. Duplicate submissions create only one review and never cause a 500
   error.
   3. Product averages and counts include only published reviews.

   However, before implementation, please investigate why /implement is not
   available. We previously created and committed
   .claude/skills/implement/SKILL.md during the Wishlist assignment.

   Check whether that file exists, whether its YAML frontmatter is valid,
   and whether Claude Code needs a session restart or reload to discover it.
   Do not overwrite the existing skill or recreate it unnecessarily.

   Stop and tell me what you find and the exact next step. Do not write
   application code, run migrations, or begin RED/GREEN cycles yet.
6. /implement @prd/product-reviews.md @plans/product-reviews.md implement
   phase 1
7. pprove the first RED test exactly as written, including all elgilbility
   scenarios. Proceed with GREEN for behavior 1 only. wtite the minimum code
8. I approve GREEN for Behavior 1. All seven eligibility cases pass, the
   full 559-test regression suite passes, and Ruff is clean.

   Continue Phase 1 by adding the remaining can_create safeguards for
   anonymous users and customers who already have a review, with normal
   tests. Build the minimum create-view and form skeleton needed for
   Behavior 2.

   Then write and run the RED test for Behavior 2: repeated or concurrent
   review submissions must not create duplicate reviews or produce an HTTP
   500 error.

   Stop after reporting the RED test and its expected assertion failure. Do
   not implement GREEN for Behavior 2 until I approve it.

   Do not migrate or seed my development database, touch either backup,
   commit, push, or begin another phase.
9. I approve the Behavior 2 RED test, including both repeated and simulated
   concurrent submissions.

   I approve redirecting customers who already have a review with the
   message "You've already reviewed this product" instead of returning 403
   for duplicate create attempts. Other unauthorized authenticated users
   must still receive 403.

   I also approve the deterministic pre_save-hook simulation of the race
   condition.

   Proceed with GREEN for Behavior 2 only. Handle the unique constraint race
   inside an appropriate transaction/savepoint, catch only the relevant
   duplicate-review IntegrityError, and do not hide unrelated database
   errors. Ensure that the existing review's rating and comment are never
   overwritten.

   Run both Behavior 2 cases, relevant regressions, and Ruff checks. Report
   the results and STOP for my GREEN approval before starting Behavior 3.

   Do not migrate or seed db.sqlite3, touch either backup, commit, or push.
10. I choose Option 1. I approve changing the concurrent-submission test to
    insert the competing review after form validation but before the
    transaction.atomic() savepoint, so the winning review survives the
    losing insert's rollback.

    Keep all four original test assertions unchanged. Keep the production
    savepoint and the safeguard that unrelated IntegrityErrors must be
    re-raised.

    Also inspect reviews/views.py carefully: the displayed diff appears to
    contain response = super().form_valid(form) both before the try block
    and inside transaction.atomic(). Make sure the final code calls
    super().form_valid(form) only once, inside the savepoint. Do not
    accidentally save the form twice.

    Rerun both duplicate-submission cases, relevant regression tests, and
    Ruff. If GREEN is reached, report the exact results and STOP for my
    approval before starting Behavior 3.

    Do not migrate or seed my development database, touch either backup,
    commit, or push.
11. *(A copy of the agent's previous update, pasted back with no new
    instructions: its note that `super().form_valid(form)` appears only
    once, the displayed diff of the `other_tab_wins` fixture change, and
    "The full suite is running.")*
12. I approve GREEN for Behavior 2. Both duplicate-submission cases pass,
    the full 564-test suite passes, and Ruff is clean.

    Proceed to Behavior 3: published-only average ratings and review counts
    on the product detail page.

    Build only the minimal supporting skeleton normally, then write and run
    the Behavior 3 RED test. Include a published review and a hidden review
    to prove that only published reviews contribute to the average and
    count, with the displayed average rounded to one decimal place.

    Stop after demonstrating the expected RED assertion failure. Do not
    implement GREEN until I approve it.

    During the remaining normal Phase 1 work, also add a regression test
    proving unrelated IntegrityErrors are re-raised rather than silently
    handled as duplicate reviews.

    Do not migrate or seed db.sqlite3, touch either backup, commit, push, or
    start Phase 2.
13. I approve the Behavior 3 RED test exactly as written.

    Proceed with GREEN for Behavior 3 only. Implement
    Review.objects.summary_for(product) using only published reviews,
    computing their average and count efficiently. Keep the approved
    one-decimal display and zero-review empty state.

    Run the Behavior 3 test, relevant regression tests, the full suite, Ruff
    lint, and Ruff formatting checks. Report exact results and stop for my
    GREEN approval before starting the remaining Phase 1 work.

    Remember to add the unrelated IntegrityError regression test during the
    remaining normal Phase 1 work.

    Do not apply migrations or run seed against db.sqlite3, touch either
    database backup, commit, push, or begin Phase 2.
14. I approve GREEN for Behavior 3. The full 565-test suite passes, and Ruff
    lint and formatting checks are clean.

    All three planned TDD cycles for Phase 1 are complete. Proceed with the
    remaining normal Phase 1 implementation according to
    prd/product-reviews.md and plans/product-reviews.md.

    Complete the accessible DaisyUI star form, product detail review
    section, published review display, Verified buyer bylines,
    visitor-specific eligibility states, pinned Your review display,
    zero-review empty state, and ReviewAdmin. Add model, view,
    authorization, escaping, validation, and regression tests, including
    proving unrelated IntegrityErrors are re-raised.

    Implement only Phase 1. Do not begin editing/deleting review
    functionality planned for Phase 2 or moderation planned for Phase 4.

    Run the full test suite, Ruff lint, Ruff formatting, and migration
    checks. Fix any failures.

    Then STOP before applying any migrations to db.sqlite3. Give me the safe
    PowerShell instructions to create db.sqlite3.before-reviews-backup
    without overwriting an existing backup. Wait for my confirmation before
    migrating or proceeding to browser verification.

    Do not run seed, touch the wishlist backup, commit, or push.
15. Please perform a READ-ONLY inspection of my existing development
    database. Find regular (non-staff, non-superuser) customer accounts with
    Delivered orders and identify the exact products in those orders.
    Report only the usernames, order statuses, and product names/slugs. Do
    not display passwords, hashes, emails, or other sensitive details.

    Do not create, modify, delete, seed, or reset any records. Do not run
    migrations, commit, or push. Stop after reporting the eligible accounts
    and products so I can choose how to test Phase 1 in my browser.
16. Phase 1 browser verification: I signed in as the existing customer
    account, submitted a 4-star MindSync review, and confirmed the product
    page displays a 4.0 average, 1 review, the pinned Your review section,
    Verified buyer, and the correct comment. Functionality works.

    However, on the review form, the five rating controls render as small
    gray circles instead of visible stars. Please investigate the actual
    template, DaisyUI classes, and currently compiled CSS. Fix only this
    presentation issue, ideally with existing CSS or an accessible
    no-JavaScript fallback. Preserve radio-group keyboard accessibility,
    rating values, and form validation.

    Do not disable Windows security controls or rely on running the blocked
    Tailwind executable. Do not seed, reset, or modify existing database
    records. Run focused tests, the full suite, and Ruff checks after any
    code changes. Stop and report what changed before any commit or push.
    Stay in Phase 1.
17. Phase 1 browser verification is complete: staff, anonymous, ineligible
    and eligible customer states were checked; a 4-star MindSync review
    submitted successfully; the public rating, count, Verified buyer byline
    and pinned Your review all displayed correctly. The SyncRest form now
    visually displays all five star choices. I will also confirm native
    radio selection in the browser.

    Please complete the Phase 1 PROMPTS.md documentation required by the
    /implement workflow. Then run git status and show me the exact proposed
    files to stage, their changes, and any untracked files. Verify the final
    full test suite, Ruff, and migration checks remain clean.

    Do not stage, commit, push, seed, reset, or alter database records.
    Explicitly exclude db.sqlite3, db.sqlite3.before-wishlist-backup, and
    db.sqlite3.before-reviews-backup. Stop for my approval of the staging
    list.

### Summary
- **Outcome:** the PRD is final, the six-phase plan is saved, and Phase 1 is
  built. A customer who received a product can review it, and everyone can
  see published reviews on the product page.
  - **PRD (prompts 1–2):** the "more than 10 seeded reviews on one product"
    goal could not be met. The agent replayed the seed's fixed-seed order
    RNG in plain Python, without touching a database. At most **five**
    distinct customers have a Delivered order for any one product, and the
    seed has only 10 regular customers in total. The developer removed the
    requirement and kept 10 reviews per page. Pagination will be proven by
    pytest fixtures with 11 or more reviewers. The "Unresolved Constraints"
    section became "Resolved Constraints", and the four confirmed defaults
    are recorded there.
  - **Plan (prompt 3):** `plans/product-reviews.md` has six phases, with
    Phases 4 and 5 kept separate. Phase 6 (seed) is verified by tests only.
    Phase 1 creates the complete `Review` model and `published()` so later
    phases need no further `Review` migration.
  - **TDD (prompts 5–13):** three approved behaviors, each RED on an
    assertion, then GREEN with the full suite run:
    1. `can_create`: only a regular customer with a Delivered order of
       this exact product record qualifies. One parametrized test covers
       seven cases.
    2. Duplicate submissions: one row, a redirect with "You've already
       reviewed this product.", never a 500. The save runs in a savepoint,
       and an `IntegrityError` is handled only when the customer's review
       now exists; anything else is re-raised.
    3. `summary_for`: the average and count use published reviews only, in
       one aggregate query, and the average is shown to one decimal.
  - **Normal Phase 1 work (prompt 14):**
    - The `reviews` app: model, migration `0001_initial` (creates only
      `reviews_review`), `ReviewForm`, `ReviewCreateView` at
      `/products/<slug>/review/`, and `ReviewAdmin` with the moderation
      fields read-only.
    - `visitor_state()` and the `star_glyphs` filter, which rounds to the
      nearest half.
    - The product page's `#reviews` section: "Verified buyer" bylines, the
      pinned "Your review", every Phase 1 visitor state, and the empty
      state.
    - 69 new tests, including the regression test that an unrelated
      `IntegrityError` is re-raised. Final checks: 634 tests passed; Ruff
      lint and format and `makemigrations --check` were clean.
  - **Browser verification (prompts 16–17):** done by the developer as
    `customer`, staff, anonymous and ineligible visitors. Native radio
    selection was still to be confirmed.
- **Deviations:**
  - A customer who already has a review is redirected with a message
    rather than given 403 (approved in prompt 9). Everyone else who isn't
    allowed still gets 403.
  - The race simulation moved from a `pre_save` hook to wrapping
    `ReviewForm.clean` (Option 1, prompt 10).
  - The PRD and plan say the stars are "styled with DaisyUI `rating`". The
    form now uses native DaisyUI `radio` inputs with star glyphs and
    visible "N stars" labels instead (prompt 16). The PRD and plan text
    were not updated.
  - `/implement`'s final step says to commit **and push**. The developer's
    standing instruction is to stop for approval first, so nothing has been
    committed.
  - The `CLAUDE.md` update for the `reviews` app is still deferred, as the
    PRD says.
- **Sideways:**
  - **`/implement` didn't run at first (prompt 4).** The skill sets
    `disable-model-invocation: true`, so only a typed slash command starts
    it, and a slash command inside pasted text arrives as plain text. The
    file and its frontmatter were fine and no restart was needed (prompt
    5). Typing the command (prompt 6) worked.
  - **The approved race simulation couldn't pass.** The `pre_save` hook ran
    inside the view's savepoint, so the "other tab's" row was rolled back
    with the losing insert. The re-check then found no review and correctly
    re-raised. The agent stopped, did not loosen the error handling, and
    offered two options. Moving the hook to `ReviewForm.clean` fixed it
    with the four assertions unchanged.
  - **A diff display looked like a double save.** The developer read the
    edit's before/after display as two calls to `super().form_valid(form)`
    (prompt 10). Reading the file showed one call, inside the savepoint.
  - **The model didn't enforce the comment limit.** A new test showed that
    `TextField(max_length=2000)` only limits the form. The agent added a
    `MaxLengthValidator` and regenerated the unapplied, uncommitted
    `0001_initial.py` instead of adding a second migration.
  - **Migrations were never run against the real database.** `makemigrations`
    and its `--check` ran against an in-memory database, so `db.sqlite3`
    wasn't opened during implementation.
  - **The migration was applied outside the agent.** During the read-only
    inspection (prompt 15), `db.sqlite3` had a new modification time. Read-
    only queries showed `reviews.0001_initial` applied at 17:11 UTC and a
    sign-in at 17:41 UTC, neither run by the agent. They also showed
    `db.sqlite3.before-reviews-backup` with the pre-migration size and
    timestamp. The agent reported this rather than assuming who did it.
  - **The stars rendered as gray circles (prompt 16).** The compiled
    `tailwind.css` dated from Oct 11 and had none of the new DaisyUI
    `rating`/`mask` classes, and the Tailwind build is blocked on this
    machine. Several layout utilities the new templates used were missing
    too. Every class in the reviews templates was checked against the
    compiled CSS, and the missing ones were replaced with ones already
    there. The agent did not add an automated CSS check, because
    `tailwind.css` is not committed.

## 2026-10-16 — Wishlist Phase 3: demo wishlist in seed

### Prompts
The same agent session as the Phases 1 and 2 entry below, which records
prompts 1–15. Prompt text is verbatim. Prompt 1 approved the Phases 1–2
commit; it is recorded here because that entry was already committed.

1. I approve the proposed Wishlist Phases 1–2 commit and commit message.
   Stage only the explicitly reviewed wishlist files, including the PRD,
   plan, both skills, implementation code, templates, tests, and
   PROMPTS.md. Do not use git add -A or git add .

   Before committing, run git diff --cached --name-only and git diff
   --cached --stat. Confirm the staged list contains exactly the intended
   files and excludes db.sqlite3 and db.sqlite3.before-wishlist-backup. If
   there is any unexpected file, stop and ask me before proceeding.

   If the staged files are correct, commit the changes and push to
   origin/main. Then show me git status, git log -1 --oneline, and
   confirmation of the push. Do not start Phase 3 implementation yet.
2. Go ahead and continue /implement for Wishlist Phase 3 using
   @prd/wishlist.md and @plans/wishlist.md.

   The Phase 3 TDD skip is approved. Implement only Phase 3: demo wishlist
   seed data, fixed added_at timestamps, wipe behavior, success message,
   README documentation, and automated tests for contents, order, wipe,
   and repeatability.

   Run seed only in the isolated test database. Do not run the seed
   command against my development db.sqlite3, and do not modify, delete,
   or reset db.sqlite3 or db.sqlite3.before-wishlist-backup.

   Run the full test suite, Ruff lint, and formatting checks. Fix any
   failures.

   Then give me the manual verification instructions and STOP for my
   approval, as required by /implement. Do not commit, push, or start the
   product reviews homework yet.
3. Phase 3 looks good, and I approve using isolated automated tests
   instead of running seed against my personal development database.

   Before final approval, please check the exact Phase 3 requirement in
   prd/wishlist.md and plans/wishlist.md for added_at timestamps. If the
   approved requirement calls for literal fixed timestamps, change the
   demo wishlist timestamps to fixed timezone-aware calendar dates rather
   than offsets from timezone.now(). Keep the newest-first order and all
   other intended behavior.

   Update tests as necessary, rerun the full pytest suite, Ruff lint, and
   Ruff format checks. Do not run seed against db.sqlite3, and do not
   touch the database backup or media files.

   Then report the results and stop for my approval. Do not commit or push
   yet.
4. I approve Wishlist Phase 3. The corrected fixed UTC timestamps meet the
   PRD and plan, all 552 tests pass, Ruff checks are clean, and I approve
   isolated automated verification instead of running seed against my
   development database.

   Please complete /implement Step 5:
   1. Add an accurate Phase 3 entry to PROMPTS.md using its existing
   format.
   2. Review git status and show me the exact files proposed for the Phase
   3 commit, including PROMPTS.md.
   3. Exclude db.sqlite3, db.sqlite3.before-wishlist-backup, media files,
   and unrelated changes.
   4. Stop and wait for my approval of the staged file list before
   committing or pushing.

   Do not start the product reviews homework yet.

### Summary
- **Outcome:** after `seed`, the demo `customer` login has a four-item
  wishlist, and every run gives the same one.
  - **Phases 1–2 commit (prompt 1):** the 26 reviewed files were staged by
    path. `git diff --cached` confirmed no database files. The commit is
    `17940cc` and was pushed to `origin/main`. The agent had earlier said
    29 files; the real count was 26, all from the reviewed list. The
    miscount was disclosed before committing.
  - **TDD skipped:** `/tdd` found no candidates, because Phase 3 is only
    seed data and documentation. The developer approved skipping it.
  - **`products/management/commands/seed.py`:** `CUSTOMER_WISHLIST` lists
    MindSync Duo, Pulse Halo and RecallPro, plus EchoPatch, which is
    unavailable. Each has a fixed UTC `added_at`, from 2026-10-14 back to
    2026-09-15. `_create_customer_wishlist()` creates the items directly,
    because `save_product()` would refuse the unavailable EchoPatch.
    `_wipe()` now deletes every `Wishlist` row after the carts. The success
    message reports "a 4-item wishlist", and the module docstring mentions
    the wishlist.
  - **`README.md`:** the `customer` demo login now mentions the wishlist and
    its unavailable item.
  - **Tests (`products/tests.py`):**
    - The exact `(slug, added_at)` pairs, newest first, with EchoPatch as
      the only unavailable item.
    - Identical values after running `seed` twice.
    - Wishlist and item counts added to the idempotence test.
    - Only the demo wishlist is left after seeding, even when a user the
      seed doesn't manage had one. Removing the new wipe line made this
      test fail; the line was then restored.
    - The success message mentions the wishlist.
    - The existing `test_seed_sends_nothing` still covers email.
  - **Verification:** 552 tests passed; `ruff check` and
    `ruff format --check` were clean. The developer approved automated
    verification instead of a browser check (prompt 3).
  - **Data safety:** `seed` ran only inside the test suite's own database.
    `db.sqlite3`, `db.sqlite3.before-wishlist-backup` and `media/` kept
    their earlier sizes and modification times.
- **Deviations:**
  - The browser check was replaced by automated tests, at the developer's
    choice. `seed` deletes product images from `media/`, so a manual check
    would have meant backing up both the database and `media/`.
  - The `CLAUDE.md` project-layout update is still deferred, as the PRD
    says.
- **Sideways:**
  - The first build dated the demo items as days before the moment `seed`
    ran, the way seeded orders are dated. When reporting it, the agent
    flagged that this differs from the PRD's "fixed `added_at` times". In
    prompt 3 the developer asked for a check. The plan's acceptance
    criterion ("The items' `added_at` values are fixed") requires literal
    values, so the agent switched to fixed UTC datetimes. The repeatability
    test now compares the stored values, not just the order. The agent
    reasoned that this stronger test would have failed on the first
    version, because the stored times include microseconds and differ
    between runs, but did not run it against that version.

## 2026-10-16 — Wishlist Phases 1 and 2: save/remove button, wishlist page, /tdd and /implement skills

### Prompts
One agent session, which began after `/clear`. Prompt text is verbatim,
except that the three pasted skill texts (prompts 3, 4 and 11) are not
repeated here: prompt 3 held only the `tdd` frontmatter, and prompts 4 and
11 are saved word for word as `.claude/skills/tdd/SKILL.md` and
`.claude/skills/implement/SKILL.md`. Prompt 5 is the `/tdd` command.

1. @prd/wishlist.md @plans/wishlist.md Implement Phase 1 only.

   Follow the approved wishlist plan and the existing ThoughtTronix
   conventions. Build the wishlist models, migrations, save/remove POST
   views, HTMX button, authentication, authorization, Django admin
   registration, and all required button states, including unavailable
   products.

   Use the project's existing testing process for Phase 1. Do not use /tdd
   yet. Run the full pytest suite and Ruff linting and formatting checks.

   Do not implement Phase 2 or Phase 3. Do not run the seed command against
   my development database, and do not reset or delete db.sqlite3.

   When Phase 1 is implemented, explain how I can manually verify every
   acceptance criterion in the browser. Stop and wait for my approval
   before continuing. Do not commit or push yet.
2. Phase 1 of the ThoughtTronix wishlist is manually verified and
   approved. Before starting Phase 2, create .claude/skills/tdd/SKILL.md
   using the exact TDD skill instructions from Lesson 10 that I will paste
   next. Do not invent a replacement skill or begin implementing Phase 2.
   First confirm that you're ready for me to paste the full skill text.
3. *(pasted the `tdd` skill's frontmatter only)*
4. *(pasted the full `tdd` skill text)*
5. /tdd @prd/wishlist.md @plans/wishlist.md implement phase 2
6. I approve both TDD behaviors for Phase 2: (1) displaying only the
   signed-in user's own saved products, and (2) showing a designed empty
   state without creating a Wishlist record. Build only the necessary page
   skeleton first, then follow the /tdd skill exactly. Write and run one
   test at a time, demonstrate a genuine assertion failure (RED), show me
   the test and explain what passing it will prove, and stop for my
   approval before writing the implementation. Make sure newest-first
   ordering and all remaining Phase 2 acceptance criteria are implemented
   and tested normally. Do not begin Phase 3, run seed, or modify
   db.sqlite3 unnecessarily.
7. I approve the first RED test. It correctly verifies that the signed-in
   customer sees their own saved product and not another customer's
   product. The assertion failure is caused by the missing wishlist
   listing behavior, not a setup error. Please proceed with the GREEN
   step: implement only enough functionality to make this approved test
   pass, run the test again, and run the relevant regression tests. Then
   explain what changed and pause for my review before moving to the next
   behavior.
8. I approve GREEN for Behavior 1. The test passed, the relevant
   regression tests passed, and filtering WishlistItem through
   wishlist__user=self.request.user implements the actual ownership rule
   rather than merely satisfying the test with hardcoded data. Please
   proceed to Behavior 2 using the /tdd skill. Write one test for the
   empty state and read-only behavior, run it to demonstrate a genuine
   assertion failure (RED), show me the failing test and explain why it
   failed, and stop for my approval before implementing the behavior.
9. I approve the second RED test. The assertion failure correctly
   demonstrates that the empty-state message is missing, while the test
   also protects the requirement that viewing the page must not create a
   Wishlist record. Please proceed with GREEN by implementing only enough
   code to make this approved test pass. Rerun the test and relevant
   regression tests, then explain what changed and stop for my approval
   before implementing the remaining Phase 2 requirements.
10. I approve GREEN for Behavior 2. The test now passes, the 101
    regression tests pass, and the {% empty %} branch implements the
    intended behavior rather than hardcoding the test case.

    Both approved TDD behaviors are complete. Please finish the remaining
    Phase 2 acceptance criteria using the project's normal implementation
    and testing process, including newest-first ordering, product images,
    names, prices, availability, detail-page links, an appropriately
    designed empty state, the signed-in-only Wishlist navbar link, and
    authentication and query-efficiency tests.

    Run the full pytest suite and Ruff linting and formatting checks. Do
    not implement Phase 3, run seed, or modify or reset db.sqlite3. When
    Phase 2 is ready, provide step-by-step browser verification
    instructions and stop for my approval. Do not commit or push yet.
11. *(pasted the full `implement` skill text, with no instruction)*
12. Yes to both questions.

    1. Save the /implement skill exactly as I provided it to
    .claude/skills/implement/SKILL.md. Do not execute it yet. Confirm the
    file contains all five sections and the correct frontmatter.

    2. I confirm that Wishlist Phase 2 passed manual browser verification
    and is approved. Phase 1 was also manually verified and approved.

    Before committing, please review git status and git diff, identify all
    intended uncommitted work from Wishlist Phases 1 and 2, including the
    PRD, plan, and /tdd and /implement skills. Update PROMPTS.md using its
    existing conventions and review the proposed staged-file list with me.

    Do not stage, reset, delete, or commit db.sqlite3 or
    db.sqlite3.before-wishlist-backup. Do not include unrelated files. Stop
    and wait for my approval of the exact commit contents before creating
    or pushing any commits. Do not start Phase 3 yet.
13. /implement @prd/wishlist.md @plans/wishlist.md implement phase 3
14. Pastd text #10 +8 lines]
15. I approve skipping TDD for Phase 3 because it only involves demo seed
    data and documentation, which are not appropriate for test-first
    development under our /tdd skill.

    Before implementing Phase 3, let's finish committing Phases 1 and 2.
    Both phases passed manual browser verification and are approved.

    Please review git status, git diff, and the intended files from Phases
    1 and 2, including prd/wishlist.md, plans/wishlist.md, the /tdd and
    /implement skills, application code, tests, and PROMPTS.md.

    Show me the exact files you intend to stage and the proposed commit
    message. Do not commit or push until I approve that list.

    Do not stage, modify, reset, delete, or commit db.sqlite3 or
    db.sqlite3.before-wishlist-backup. Do not include unrelated files or
    start Phase 3 implementation yet.

### Summary
- **Outcome:** signed-in shoppers can save and remove products from the
  product page without a reload, and see everything they saved on a new
  Wishlist page. Phase 3 (the demo wishlist in `seed`) is not started.
  - **Phase 1 (built with the normal process, no `/tdd`):** a new
    `wishlist` app. `Wishlist` is one per user and is created only by
    `for_user()`. `WishlistItem` has `added_at`, newest-first ordering and
    the `unique_wishlist_product` constraint. Three model methods:
    `save_product()` (saving twice keeps one item), `Wishlist.remove_for()`
    (harmless when nothing is saved) and the read-only
    `Wishlist.has_saved()` (never creates a wishlist). The initial migration
    is `wishlist/migrations/0001_initial.py`. `wishlist:save` and
    `wishlist:remove` are POST-only, sign-in-required views sharing one base
    view, and they act only through `request.user`. Save looks products up
    through `available()`, so an unavailable or unknown product is a 404;
    remove looks among all products. The button partial
    `_wishlist_button.html` has all four states, with `aria-pressed`, the
    hearts hidden from screen readers, and a stable `id="wishlist-button"`.
    It sits beside add-to-cart, and `ProductDetailView` supplies `saved`.
    `WishlistAdmin` has an item inline and search by username. New
    `conftest.py` fixtures: `other_customer`, `wishlist`, `saved_item`.
    Result: 538 tests passed; Ruff was clean after formatting two files.
  - **Skills:** `.claude/skills/tdd/SKILL.md` (prompt 4) and
    `.claude/skills/implement/SKILL.md` (prompt 12), saved exactly as
    pasted. `implement` was not run.
  - **Phase 2 with `/tdd`:** the skill proposed two behaviors, which the
    developer approved. The skeleton (route, `LoginRequiredMixin` view, and
    a page shell extending `base.html`) was built first.
    - Behavior 1, privacy: the test failed on
      `assert 'Seraphine Home Hub' in …`. GREEN was a `ListView` filtering
      `WishlistItem` by `wishlist__user=request.user`.
    - Behavior 2, empty state without creating a wishlist: the test failed
      on `assert 'Your wishlist is empty' in …`. GREEN was an `{% empty %}`
      branch.
    - Each RED, GREEN and regression run stopped for the developer's
      approval.
  - **Phase 2, built normally:**
    - The page is a DaisyUI card grid showing image, name, price,
      availability, saved date and links to each product.
    - The empty state is designed, in the same style as order history.
    - `select_related("product__category")` loads each item's product and
      category in the same query.
    - The navbar has a plain "Wishlist" link for signed-in users only.
    - `wishlist/test_list_page.py` covers the sign-in redirect, that viewing
      changes nothing, newest first by `added_at` against creation order,
      each card's contents, an empty but existing wishlist, a constant query
      count, and the navbar link signed in and out.
    - The query-count test was checked by removing `select_related` (14
      queries against 6) and then restoring it.
    - Result: 548 tests passed; `ruff check` and `ruff format --check` were
      clean.
  - **Manual verification:** the developer reported that Phase 1 (prompt 2)
    and Phase 2 (prompt 12) both passed in the browser.
  - **Phase 3 not started:** prompt 13 ran `/implement` for Phase 3. As
    that skill requires, the agent ran `/tdd`, which found no candidates
    because the phase is only seed data and documentation. The developer
    approved skipping TDD (prompt 15) and asked to commit Phases 1 and 2
    before any Phase 3 code. The Phase 3 work will get its own entry.
  - **Data safety:** `seed` was never run. The agent never ran `migrate`; it
    told the developer to run it before the Phase 1 browser check.
    `db.sqlite3` and the developer's `db.sqlite3.before-wishlist-backup`
    are left out of the commit.
- **Deviations:**
  - The plan listed three `/tdd` candidates. The skill proposed two,
    leaving out newest-first ordering: Phase 1 had already set and tested
    `-added_at` as the model's default order, so that test could never have
    failed first. Ordering was tested normally instead, and the developer
    approved the two-behavior selection.
  - The `CLAUDE.md` project-layout update stays deferred, as the PRD says.
- **Sideways:**
  - The first `tdd` paste (prompt 3) held only the frontmatter. The agent
    asked for the rest instead of saving a partial skill.
  - Prompt 11 pasted the `implement` skill with no instruction. The agent
    asked what to do with it, and didn't run it or commit anything.
  - Prompt 14 arrived as a paste placeholder with no content. The agent
    asked for it again and changed nothing; prompt 15 is the resent
    message.
  - A `sed` edit to add the button `id` failed on quoting, so the partial
    was rewritten in full instead.
  - The Phase 2 navbar link broke the Phase 1 test
    `test_back_office_has_no_wishlist_screen`, which had looked for the
    word "wishlist" anywhere on the back-office page. The agent saw this
    before running the suite and narrowed the test to the back office's own
    content below the navbar, which still has no wishlist tab or screen.
  - `ruff format` reformatted `conftest.py` and `products/tests.py` in
    Phase 1, and `wishlist/test_list_page.py` in Phase 2. All three were
    reformatted before the final checks.

## 2026-10-16 — Account Security fix: reset links copied from the console work

### Prompts
One agent session. Prompt text is verbatim. Prompt 1 started a wishlist
design interview that was paused after its first question when prompt 2
arrived; no wishlist code or documentation was written.

1. /grill-me ThoughtTronix wants customers to have one private wishlist
   each. Signed-in customers should be able to save or remove products
   from their wishlist on the product detail page without a full-page
   reload. The button should update to reflect whether the product is
   saved. Customers must only access and modify their own wishlist.
   Multiple, named, and shared wishlists are out of scope. Help me make the
   design decisions using existing ThoughtTronix patterns. Do not write
   code or documentation yet.
2. My professor reviewed Homework 6 (Account Security) and reported that
   the password reset link fails in the terminal. Investigate the existing
   password reset implementation and identify the root cause. Fix the
   issue using the project's existing conventions without changing
   unrelated features. Run the relevant tests and Ruff checks. Then give me
   step-by-step instructions to manually verify the complete password
   reset process in the browser. Do not commit or push changes yet. Do not
   modify or reset db.sqlite3.
3. I completed manual browser verification of the Homework 6 Account
   Security fix. The password reset link opened successfully, the new
   password was accepted, and the password-change notification appeared. I
   also verified that signing out of other devices invalidated the
   InPrivate browser session while keeping my regular browser session
   active.

   Please review the changes, run the relevant tests and Ruff checks, and
   update PROMPTS.md using its existing format. Then commit the completed
   Account Security fix and push it to GitHub.

   Do not include db.sqlite3 in the commit because it was already modified
   before this session. Do not reset or delete the database. Do not
   include unrelated changes. Show me the final Git status and latest
   commit.

### Summary
- **Outcome:** a password-reset link printed on the console can now be
  copied straight into the browser.
  - **Root cause:** at host `127.0.0.1:8000` the reset link is 80
    characters (Django's token alone is 39). Python's email library, which
    Django 6 uses, sends any body line over 78 characters as
    quoted-printable, and Django's stock console backend prints the email
    as encoded for the wire. The link therefore appeared with an `=` soft
    break inside the token. Copying the first line gave a cut-off token
    with no trailing slash: a 301, then "Invalid reset link". The reset
    logic itself was correct. Removing the email's non-ASCII em dash would
    not have helped, because the link line alone is long enough.
  - `config/mail.py` (new): `EmailBackend` subclasses Django's console
    backend and prints each message under an email policy with no line
    limit that allows 8-bit text, so the body prints exactly as written.
    This applies to every email: reset, password-changed, and
    email-changed. Characters the terminal's encoding can't show are
    replaced instead of raising, because the plain-text output (unlike
    quoted-printable, which is pure ASCII) could otherwise crash a request
    on a cp1252 Windows console. Links are ASCII, so they always print
    intact.
  - `config/settings.py`: `EMAIL_BACKEND = "config.mail.EmailBackend"`.
    Email still goes only to the console, as the PRD requires.
  - `CLAUDE.md`: the `EMAIL_BACKEND` note now names the project's console
    subclass.
  - Tests: three new tests in `accounts/test_password_reset_confirm.py`.
    The console prints the link whole on one line; a link copied from the
    console output resets the password with no 301 detour; and a cp1252
    stream still gets the link for a username it can't encode. The
    settings test now checks that the backend is a console backend
    subclass instead of the stock dotted path. The comments on the existing
    wire-format tests were updated; those tests still pass unchanged.
  - Verification: 492 tests passed; `ruff check` and `ruff format --check`
    were clean. `db.sqlite3` was already modified before the session and
    was not touched; every reproduction used an in-memory database.
  - Manual browser verification (prompt 3, reported by the developer): the
    reset link opened, the new password was accepted, and the
    password-changed notice appeared. Signing out of other devices ended
    the InPrivate session and kept the regular browser signed in.
- **Deviations:** the Phase 4 session had chosen not to build a custom
  backend because `CLAUDE.md` says `EMAIL_BACKEND` is always the console
  backend. This session read a subclass of the console backend as still
  meeting that rule, and updated the `CLAUDE.md` line to say so.
- **Sideways:**
  - The agent first suspected the em dash. Running the real reset view
    showed the 80-character link forces quoted-printable on its own, so the
    fix moved from the template to the backend.
  - The first fix printed the em dash as `�` in the agent's cp1252 shell,
    which exposed the crash risk above. The encoding guard and its test
    were added in response.
  - The agent's first check that the new cp1252 test fails without the
    guard was invalid: the test was missing the `db` fixture and failed
    for that reason instead. The full suite caught it. After the fixture
    was added, the check was rerun: without the guard the test fails with
    `UnicodeEncodeError`, and with the guard it passes.

## 2026-10-11 — Account Security Center Phase 7: sign out of all other devices

### Prompts
Phase 7 ran in one agent session, which began after `/clear`. Prompt text
is verbatim. Prompt 2 arrived cut off mid-sentence; it is recorded as
received.

1. @prd/account-security.md @plans/account-security.md

   Implement Phase 7 only: Sign Out Other Devices.

   Follow the approved PRD and tracer-bullet implementation plan,
   especially the Phase 7 user stories and acceptance criteria.

   Allow authenticated customers, employees, and administrators to sign
   out their other active sessions from the Account Security Center
   without signing out their current browser.

   Requirements:
   - Add a Devices card to the Security overview with a "Sign out other
     devices" action.
   - Require the user's current password before performing the action.
   - Use a per-user session salt or version mechanism, as specified in the
     approved plan, to invalidate the user's other sessions.
   - Keep the current browser signed in by updating its authentication
     session hash.
   - Do not change the user's password or email address.
   - Do not affect sessions belonging to other users.
   - Require authentication, CSRF protection, and a POST request for the
     actual sign-out action.
   - Show a clear success message after completion.
   - Preserve all functionality from Phases 1–6.

   Add automated tests covering invalid passwords, current-session
   preservation, other-session invalidation, user isolation,
   customer/staff/admin access, anonymous access, and any relevant Phase 7
   security edge cases.

   Run the full pytest suite, Ruff lint and formatting checks, Django
   system checks, and migration checks.

   Review every Phase 7 acceptance criterion and give me clear
   instructions for testing the feature manually in two separate browser
   sessions.

   Do not commit anything yet.

   Preserve my modified db.sqlite3 and all local test accounts. I want to
   review and manually test Phase 7 before committing.
2. Phase 7 implementation is complete, and I approve moving forward
   without additional manual browser testing.

   I visually verified that the Security page displays the Devices card
   and its "Sign out of all other devices" button.

   I am choosing to skip the two-browser manual test because automated
   tests already cover session invalidation and current-session
   preservation.

   Please document this accurately in PROMPTS.md. Do not claim that the
   skipped manual tests passed.

   Include the exact prompts, implementation summary, automated
   verification, migration details, issues, and deviations.

   Run the full pytest suite, Ruff checks, Django system checks, and
   migration checks.

   Review git status and stage only the intended Phase

### Summary
- **Outcome:** "Sign out of all other devices" is now available from the
  Security page, for customers, staff, and admin alike.
  - `accounts/models.py`: `User` gains `session_salt`, a
    `CharField(max_length=32, editable=False)` whose callable default,
    `new_session_salt()`, returns `secrets.token_hex(16)`. Because it is not
    editable, it never appears in the Django admin. `get_session_auth_hash()`
    and `get_session_auth_fallback_hash()` (the `SECRET_KEY_FALLBACKS`
    variant) both return an HMAC-SHA256 of `"<password hash>:<salt>"`, so
    the session hash still changes with the password and now also with the
    salt. `sign_out_other_sessions()` gives the user a new salt and saves
    only that field.
  - `accounts/forms.py`: the current-password field and its check moved
    out of `ChangeEmailForm` into a new `CurrentPasswordForm` base, built
    for one user. `SignOutOtherDevicesForm` is that base with nothing
    added, so it asks only for the current password. `ChangeEmailForm` now
    subclasses the base and sets `field_order = ["email",
    "current_password"]` so its fields stay in the same order. The error
    text is unchanged: "Your current password was entered incorrectly.
    Please enter it again."
  - `accounts/views.py`: `SignOutOtherDevicesView` is `LoginRequiredMixin` +
    `FormView` and hands the form `request.user`. A GET only shows the
    confirmation form. A valid POST calls `sign_out_other_sessions()`, then
    `update_session_auth_hash(request, user)`, which stores the new hash in
    this session and cycles its session key. It then redirects to
    `accounts:security` with "You've been signed out of all other
    devices." No email is sent. CSRF protection is Django's middleware, as
    for every other form.
  - `accounts/urls.py`: `security/devices/` → `accounts:sign_out_other_devices`.
  - `templates/accounts/security.html`: a third **Devices** card with a
    "Sign out of all other devices" button.
  - `templates/accounts/sign_out_other_devices.html`: a new confirmation
    page, built like the change-password page. It explains that this
    browser stays signed in and the password won't change, shows the
    current-password field with per-field errors, and links back to
    Security.
  - `CLAUDE.md`: the `accounts/` description notes the per-user
    `session_salt` and `sign_out_other_sessions`.
- **Migration:** `accounts/migrations/0005_user_session_salt.py`, written by
  hand.
  - `AddField` adds `session_salt` with the callable default. Django
    evaluates that default once for an `AddField`, so on its own every
    existing user would get the same value. A `RunPython` step,
    `give_each_user_their_own_salt`, then gives each existing user a fresh
    `secrets.token_hex(16)`. Its reverse is a no-op; reversing the
    migration drops the column.
  - The field stays `NOT NULL`, with no nullable intermediate step.
  - Side effect: changing how the session hash is computed signs out every
    session that existed before the migration, for every user, once.
    Passwords are unaffected, so users just sign in again. The hash-based
    design in the PRD can't avoid this.
  - `makemigrations --check --dry-run` reports no changes, so the
    hand-written migration matches the model.
  - The developer applied `0005` to their local `db.sqlite3` themselves
    before the visual check; `showmigrations` shows it applied. The agent
    did not run `migrate`, `seed`, or anything else against that database.
- **Automated tests:** `accounts/test_sign_out_other_devices.py` adds 32
  tests. Each "device" is a separate Django test `Client`, signed in on
  its own. They cover:
  - every new user and every seeded user gets a distinct, non-empty salt,
    and a seeded customer still signs in
  - the migration gives three pre-existing users three distinct salts, and
    a user created before the migration still signs in afterwards (these
    two use `MigrationExecutor`, like the Phase 1 migration tests)
  - a new salt changes the session hash but not the password hash, and a
    new password still changes the session hash
  - `session_salt` does not appear on the admin user-change page
  - the Security page has the Devices card, the button text, and the link
  - signed-out GET is redirected to login with `next`; a signed-out POST
    changes no salt and signs nobody out
  - customer, staff, and admin each get the form with only
    `current_password`, and each can sign out their other devices
  - a GET alone signs nobody out
  - a POST without a CSRF token (`enforce_csrf_checks=True`) gets a 403 and
    signs nobody out
  - a wrong, empty, or other user's password shows a field error, keeps the
    salt, keeps both devices signed in, and sends no email; the exact error
    text is shown
  - success redirects to Security with the message
  - the confirming device stays signed in (with a fresh session key) and
    two other devices of the same user are redirected to login on their
    next request; a signed-out device can sign in again
  - other users' sessions and salts are untouched, and extra `user` /
    `username` POST fields have no effect
  - the password, email, and outbox are unchanged
  - a reset link issued before the action still validates and opens the
    set-password form
  - running the action twice keeps the confirming device signed in
  - a Phase 5 password change still signs out other devices

  `accounts/test_email_identity.py` changed one line: its migration tests'
  `AFTER` target moved from `0004` to `0005`. Those tests migrate back and
  forth; finishing at `0004` would leave the test database without the new
  column for every test after them.

  Final checks (run again after this entry was written): the full suite
  passed 489 tests (457 from Phases 1–6 plus 32 new); `ruff check`,
  `ruff format --check`, `manage.py check`, and
  `makemigrations --check --dry-run` were all clean.
- **Manual verification:** the developer visually confirmed that the
  Security page shows the Devices card and its "Sign out of all other
  devices" button. The developer **chose to skip** the two-browser test the
  agent described (wrong password rejected, confirming browser stays
  signed in, the other browser sent to login, the same password still
  working, no console email, repeated for staff and admin, signed-out
  direct visit). Those steps were **not performed**. Session invalidation
  and current-session preservation are covered only by the automated
  tests above.
- **Deviations:** none from the plan's acceptance criteria. No follow-up
  questions were asked. Choices the PRD and prompts left open:
  - Prompt 1 called the action "Sign out other devices". The card button
    and page title use the PRD's wording, "Sign out of all other devices";
    the form's submit button reads "Sign out other devices".
  - The PRD says to override `get_session_auth_hash()`. The agent also
    overrode `get_session_auth_fallback_hash()`, so sessions keep working
    while a `SECRET_KEY` is being rotated. It didn't override Django's
    private `_get_session_auth_hash`. The HMAC key salt is
    `"accounts.User.get_session_auth_hash"`, not Django's own string.
  - The current-password check was moved into a shared
    `CurrentPasswordForm` base. That touches Phase 6's `ChangeEmailForm`,
    with its behavior, field order, and error text unchanged; all Phase 6
    tests still pass.
  - One Phase 1 test constant changed, as described above.
  - Prompt 2 was cut off at "stage only the intended Phase". The agent
    read it as: stage only the Phase 7 files and this file, leave
    `db.sqlite3` out, and don't commit. No commit was made.
- **Sideways:**
  - **Escaped apostrophe:** the first full accounts run failed one test.
    The success message was on the page, but Django's autoescaping had
    rendered the apostrophe as `&#x27;`. The test now compares against
    `escape(SUCCESS_MESSAGE)`.
  - **Reset-link test order:** the test for "a reset link issued before
    still works" first failed: the token was rejected. The cause was the
    test, not the feature. It issued the token and only then signed a
    client in, and `force_login` updates `last_login`, which Django builds
    reset tokens from. Any sign-in invalidates outstanding reset links,
    with or without Phase 7. The test now signs in first, then issues the
    token, then signs out the other devices, which matches the real flow.
  - **Messy first draft:** the first version of the two migration tests had
    leftover lines (a redundant model alias and a password hash computed
    twice). The agent cleaned these up, using `make_password`, before the
    first run.
  - **Phase 1 migration tests:** the agent noticed before the first run
    that they would end at `0004` and break later tests, and changed their
    target to `0005`.
  - `ruff format` reformatted the new test file on the first full check.
    The checks were run again after that and passed.
  - **CRLF slip, repeated:** the agent edited seven existing files with a
    text-mode Python script, which wrote CRLF line endings on Windows —
    the same slip as Phases 4–5, which Phase 6 had avoided. It was caught
    with `git ls-files --eol` while preparing this entry, after the first
    full checks. All seven were converted back to LF; the diff stat was
    unchanged, and the final checks ran on the LF files.
  - `db.sqlite3` was already modified before the session. Its only change
    during the session was the developer's own `migrate`. It was not
    staged.

## 2026-10-11 — Account Security Center Phase 6: change email

### Prompts
Phase 6 ran in one agent session, which began after `/clear`. Prompt text
is verbatim.

1. @prd/account-security.md @plans/account-security.md

   Implement Phase 6 only: Change Email.

   Follow the approved PRD and tracer-bullet implementation plan,
   especially the Phase 6 user stories and acceptance criteria.

   Allow authenticated customers, employees, and administrators to change
   their own email address from the Account Security Center.

   Requirements:
   - Add a Change email button to the Email card on the Security overview.
   - Create a DaisyUI-styled form that requires the user's current password
     and new email address.
   - Normalize the new email to lowercase and enforce case-insensitive
     uniqueness using the existing model constraint.
   - Reject incorrect passwords, invalid email addresses, and emails already
     registered to another account.
   - After a successful change, redirect to Security with a clear success
     message.
   - Send a security notification to the OLD email address confirming the
     change, using the existing console email backend and
     User.send_security_notice helper.
   - Handle accounts that currently have no email address safely.
   - Ensure users can change only their own email addresses.
   - Preserve functionality from Phases 1–5.

   Create automated tests covering the Phase 6 acceptance criteria,
   including successful changes, validation errors, duplicate emails,
   notifications to the old address, and accounts without an existing
   email.

   Run pytest, Ruff checks, Django system checks, and migration checks.

   Review the acceptance criteria and explain how I can manually test the
   feature in the browser.

   Do not implement Phase 7. Do not commit anything yet.

   Preserve my modified db.sqlite3 and local test accounts. I want to
   review and manually test Phase 6 before committing.
2. Phase 6 manual browser testing is complete and passed.

   I verified:
   - The Change Email form displays correctly.
   - An incorrect current password is rejected.
   - A successful email change updates the Security page to
     dana.new@example.com.
   - The security notification is sent to the OLD email, dana@example.com,
     not the new address.
   - An email already belonging to another account is rejected.
   - A rejected duplicate-email attempt leaves my current email unchanged.

   Please update PROMPTS.md with the complete Phase 6 session history,
   including all exact prompts, the implementation summary, automated
   tests, manual testing, corrections, deviations, and any issues
   encountered.

   Run the full pytest suite, Ruff lint and formatting checks, Django
   system checks, and migration checks.

   Review git status and stage only the intended Phase 6 implementation
   files and PROMPTS.md.

   Preserve my modified db.sqlite3 and all local test accounts.

   Show me the staged files, test results, and any deviations from the PRD
   before committing.

   Do not commit anything or start Phase 7 until I approve.
3. The Phase 6 staged files and test results look good.

   Before committing, please address the identified duplicate-email race
   condition so a database uniqueness conflict is handled gracefully with a
   user-friendly form error rather than an unhandled database exception.

   Add a regression test for this specific case. Preserve the existing
   unique_lowercase_email database constraint and do not add unnecessary
   migrations.

   Run pytest, Ruff, Django system checks, and migration checks again.

   Update the Phase 6 PROMPTS.md entry with this prompt, the fix, test
   results, and any relevant implementation decisions.

   Then stage only the intended Phase 6 files and PROMPTS.md, excluding
   db.sqlite3.

   Show me the final staged file list and check results before committing.
   Do not commit or start Phase 7 until I approve.

### Summary
- **Outcome:** Change email is now available from the Security page.
  - `accounts/forms.py`: `ChangeEmailForm` is a plain `forms.Form` built
    for one user, like Django's password forms. It has two fields: "New
    email address" (an `EmailField`) and "Current password". Both use
    DaisyUI `input w-full` widgets. `clean_email` lowercases the address and
    rejects one that another account uses in any capitalization, with the
    same message as signup. The user's own account is excluded, so their
    own address in other capitals is accepted. `clean_current_password`
    checks the password with `check_password`. `save()` writes only
    `email`, and `User.save()` lowercases it as before. After prompt 3,
    `save()` also handles the duplicate-email race; see **Race-condition
    fix** below.
  - `accounts/views.py`: `ChangeEmailView` is `LoginRequiredMixin` +
    `FormView`. It hands the form `request.user`, so there is no user id in
    the URL or the form. On success it redirects to `accounts:security`
    with "Your email address has been changed to <new>.". It then sends the
    email-changed notice through `User.send_security_notice`, addressed
    explicitly to the previous email. If the address didn't change (the
    same address re-entered in other capitals), the message is "Your email
    address is unchanged." and no notice is sent. If there was no previous
    address, no notice is sent either.
  - `accounts/urls.py`: `security/email/` → `accounts:email_change`.
  - `templates/accounts/security.html`: the **Email** card gains a "Change
    email" button. It shows whether or not the account has an email.
  - `templates/accounts/email_change.html`: a new page. It shows the current
    address (or says there is none), the two fields with per-field errors,
    and a link back to Security.
  - `templates/accounts/emails/email_changed_notice.txt`: the plain-text
    notice. It has the username and the date and time of the change, says
    notices and reset links no longer go to this address, and tells the
    reader to contact ThoughtTronix staff if they didn't make the change.
    It contains no password, no reset link, and not the new address.
  - No model change and no migration.
- **Race-condition fix (prompt 3):** the agent's earlier report pointed out
  a gap. Two requests could both pass `clean_email` for the same address,
  and the second save would then hit the `unique_lowercase_email`
  constraint and raise an unhandled `IntegrityError` (a 500 page).
  - `ChangeEmailForm.save()` now saves inside `transaction.atomic()`, a
    savepoint, so the failed UPDATE doesn't break the rest of the request's
    transaction. On `IntegrityError` it puts the user's previous email back
    on the in-memory `request.user`, adds the usual "A user with that email
    address already exists." error to the `email` field, and returns
    `False`. On success it returns `True`.
  - `ChangeEmailView.form_valid` returns `form_invalid(form)` when
    `save()` returns `False`. That re-renders the form with the field
    error, with no success message and no notice.
  - The duplicate message is now built by one
    `ChangeEmailForm.duplicate_email_error()` helper, used by both
    `clean_email` and `save()`. It returns a new `ValidationError` each
    time rather than reusing one shared exception instance.
  - Decisions: the handling lives in the form, because the project's
    convention is that forms own their validation. The query check in
    `clean_email` stays, so ordinary duplicates still get the error without
    a database round trip that fails. The constraint is unchanged and no
    migration was added. `SignupForm` was left as it is (Phase 1 code
    outside this prompt's scope). It has the same theoretical race on
    account creation.
- **Automated tests:** `accounts/test_email_change.py` adds 30 tests.
  They cover:
  - the Email card's button, for users with and without an email
  - signed-out GET and POST redirected to login with `next`, and the email
    unchanged
  - customer, staff, and admin each get the styled form, and staff and
    admin can complete a change
  - extra `user`/`username` POST fields are ignored, and another user's
    password does not count as the current password
  - field errors for a wrong or empty current password, and for a blank,
    whitespace-only, invalid, taken, or taken-in-other-capitals email;
    each leaves the email unchanged and sends no email
  - the exact wording of the wrong-password and duplicate-email errors
  - the redirect to Security with the success message and the new address
    on the card
  - a mixed-case new email is stored lowercase
  - your own address in other capitals is accepted, stays lowercase, and
    sends nothing
  - the user stays signed in after the change
  - exactly one plain-text notice, addressed only to the previous email,
    with the date and no password, new address, or `/reset/` link
  - a user with no email adds one: no notice, and the no-email warning
    disappears
  - editing a user's email in the Django admin sends nothing and stores it
    lowercase
  - after a change, a reset request for the old address sends nothing and
    one for the new address sends the reset email
  - (prompt 3) a regression test for the race. It wraps the real
    `clean_email` so a rival account claims the address, in other
    capitals, right after the duplicate check passes and before the save.
    The response is a 200 with the field error, the page still shows the
    old address, there is no success message and no email, both accounts
    keep their addresses, and the user is still signed in. The agent
    checked that the test fails when the guard is removed (an unhandled
    `IntegrityError: UNIQUE constraint failed: index
    'unique_lowercase_email'`) and passes with it.

  Before prompt 3, the full suite passed 456 tests (427 from Phases 1–5
  plus 29 new). After the fix it passed 457. Both times, `ruff check`,
  `ruff format --check`, `manage.py check`, and
  `makemigrations --check --dry-run` were all clean.
- **Manual verification (developer, in the browser):** the form displays
  correctly; a wrong current password is rejected; a successful change
  updates the Security page to `dana.new@example.com`; the notice goes to
  the old address, `dana@example.com`, not the new one; an email that
  belongs to another account is rejected; and that rejected attempt leaves
  the current email unchanged. This was done before the prompt 3 fix. The
  race can't practically be triggered by hand, so only its automated test
  covers it.
- **Deviations:** none from the plan's acceptance criteria. No follow-up
  questions were asked. Choices the PRD and prompts left open, and one
  wording point:
  - Prompt 1 asked for uniqueness "using the existing model constraint".
    The form checks for a duplicate with an `email__iexact` query to give a
    friendly field error, the same way the signup form does. The existing
    `unique_lowercase_email` constraint stays as the database backstop. As
    first built, the form didn't handle that backstop firing, so if two
    requests raced for the same address, the loser would get a database
    error instead of a form error. The agent reported this, and prompt 3
    had it fixed.
  - Re-entering the current address counts as success with "Your email
    address is unchanged." and sends no notice. The PRD doesn't cover this
    case.
  - The button reads "Change email" even when the account has no email.
  - The form asks for the new email first, then the current password. That
    is the plan's order; prompt 1 listed them the other way round.
  - The success message wording and the notice's text are the agent's.
    The PRD asked only for "a confirmation message" and a notice to the
    previous address.
- **Sideways:**
  - **Notice sent to the new address:** the first version of the view
    called `send_security_notice(..., recipient=previous_email)` without a
    check. When the previous email was blank, the helper fell back to the
    user's *current* (new) email, so a staff member adding their first
    address got the notice. The new test for a user without an email
    caught this on the first run (28 passed, 1 failed). The view now sends
    only when there was a previous address. `send_security_notice` itself
    was not changed.
  - **The race condition itself**, described above: the agent left it in
    the first build and reported it as a deviation instead of fixing it.
    The developer asked for the fix before committing.
  - While fixing it, the agent first stored the duplicate error as one
    class-level `ValidationError` instance and raised that same instance
    every time. Before running any tests, it replaced this with a helper
    that builds a new error on each call, because raising a shared
    exception instance keeps adding tracebacks to it.
  - `ruff format` reformatted `accounts/forms.py` and the new test file on
    the first full check. The full checks were run again after that and
    passed.
  - Line endings: all edits were made with the editor tools, not a
    text-mode script, so the Phase 4–5 CRLF slip did not repeat.
    `git ls-files --eol` showed LF for every Phase 6 file.
  - `db.sqlite3` was already modified before the session. It was neither
    changed nor staged. The tests run on pytest's own test database.

## 2026-10-11 — Account Security Center Phase 5: change password

### Prompts
Phase 5 ran in one agent session, which began after `/clear`. Prompt text
is verbatim.

1. @prd/account-security.md @plans/account-security.md

   Implement Phase 5 only: Change Password.

   Follow the approved PRD and tracer-bullet implementation plan,
   especially the Phase 5 user stories and acceptance criteria.

   Allow authenticated customers, employees, and administrators to change
   their own passwords from the Account Security Center.

   Requirements:
   - Add a Password card to the Security overview with a working Change
     password link.
   - Use Django's built-in PasswordChangeView and PasswordChangeForm with
     DaisyUI styling.
   - Require the user's current password.
   - Require and confirm a new password that satisfies the existing Django
     password validators.
   - Show helpful validation errors for an incorrect current password,
     weak new passwords, and mismatched passwords.
   - After a successful change, redirect to the Security overview with a
     clear success message.
   - Preserve the current user's authenticated session using Django's
     update_session_auth_hash.
   - Invalidate other existing sessions through Django's normal password
     hash behavior.
   - Send a password-changed notification through the console email
     backend, reusing the Phase 4 notification helper.
   - Never include passwords in notifications.
   - Require authentication and prevent users from changing another user's
     password.
   - Preserve all functionality from Phases 1–4.

   Create automated tests for these behaviors and run the full pytest
   suite, Ruff checks, Django system checks, and migration checks.

   Review Phase 5's acceptance criteria and give me clear browser-testing
   instructions.

   Do not implement Phases 6–7. Do not commit anything yet.

   Preserve my modified db.sqlite3 and local test accounts. I want to
   manually test Phase 5 and review the changes before committing.
2. Phase 5 manual browser testing is complete and passed.

   I verified:
   - The Change Password form displays correctly.
   - An incorrect current password is rejected.
   - A valid new password successfully changes the account password.
   - The Security page displays the success message.
   - My current browser stays signed in.
   - The password-changed notification appears in the Django console.
   - A second signed-in Incognito session is signed out after the password
     change.

   Please update PROMPTS.md with the Phase 5 session history, including the
   exact prompts, implementation summary, automated tests, manual
   verification, and any issues or deviations.

   Run the full pytest suite, Ruff checks, Django system checks, and
   migration checks.

   Review git status and stage only the intended Phase 5 files and
   PROMPTS.md.

   Preserve my modified db.sqlite3 and all local test accounts.

   Show me the staged files and test results before committing. Do not
   commit anything or begin Phase 6 until I approve.

### Summary
- **Outcome:** Change password is now available from the Security page.
  - `accounts/forms.py`: `ChangePasswordForm` is Django's
    `PasswordChangeForm` with DaisyUI `input w-full` widgets. The stock
    form checks the current password and the confirmation, and runs
    `AUTH_PASSWORD_VALIDATORS`.
  - `accounts/views.py`: `ChangePasswordView` is
    `LoginRequiredMixin` + Django's `PasswordChangeView`. It sends the user
    to `accounts:security` and flashes "Your password has been changed.".
    It then sends the notice with Phase 4's `send_password_changed_notice`,
    which calls `User.send_security_notice`. Django's view already calls
    `update_session_auth_hash`, so this session survives. Every other
    session fails Django's password-hash check on its next request. The
    URL has no user id and the form is built for `request.user`, so a user
    can only change their own password.
  - `accounts/urls.py`: `security/password/` → `accounts:password_change`.
  - `templates/accounts/security.html`: a **Password** card with a
    "Change password" button.
  - `templates/accounts/password_change.html`: a new page with current,
    new, and confirm fields; per-field errors and help text; and a link
    back to Security.
  - No model change and no migration.
- **Automated tests:** `accounts/test_password_change.py` adds 22 tests.
  They cover:
  - the card's link
  - signed-out GET and POST redirected to login with `next`, and the
    password unchanged
  - customer, staff, and admin each get the styled form, and staff and
    admin can complete a change
  - extra `user`/`username` POST fields are ignored, and another user's
    password does not count as the current password
  - field errors for a wrong current password, a mismatch, a too-short
    password, a common all-numeric password, and a password too like the
    email; each leaves the password unchanged and sends no email
  - the redirect to Security with the success message
  - the new password works and the old one doesn't
  - this client stays signed in while a second client is redirected to
    login
  - exactly one plain-text notice to the current email, with the date and
    the reset-page link, and no passwords or `/reset/` link
  - a user with no email changes their password and no email is sent

  Before and after the line-ending fix, the full suite passed 427 tests. `ruff check`,
  `ruff format --check`, `manage.py check`, and
  `makemigrations --check --dry-run` were all clean.
- **Manual verification (developer, in the browser):** the form displays
  correctly; a wrong current password is rejected; a valid new password
  changes the password; the Security page shows the success message; the
  current browser stays signed in; the notice appears in the Django
  console; and a second signed-in Incognito session is signed out after
  the change.
- **Deviations:** none from the PRD, the plan, or the prompts. No follow-up
  questions were asked. Two small choices the prompts left open:
  - The view adds `LoginRequiredMixin` even though `PasswordChangeView`
    already requires login. The PRD names that mixin for every non-reset
    view, and it matches the other Security views.
  - The success message wording is "Your password has been changed.". The
    PRD asked only for "a confirmation message".
- **Sideways:**
  - **Line endings, a repeat of Phase 4's slip:** the agent edited
    `accounts/forms.py`, `accounts/urls.py`, `accounts/views.py`, and
    `templates/accounts/security.html` with an inline Python script. The
    script wrote in text mode, so Windows saved CRLF line endings. The
    encoding stayed valid UTF-8 and no text changed. The new test file and
    the `password_change.html` template were written as LF. This was
    caught before staging. A first `grep` check for `\r` gave false
    positives on untouched files, so the agent used
    `git ls-files --eol` instead. That showed `w/crlf` for exactly those
    four files. They were rewritten byte for byte as LF, and the full
    checks were run again afterward. The Phase 1–4 suite was not affected.
    The Phase 4 entry had already recorded this pitfall, but the agent
    still used a text-mode script for its first edits.
  - `db.sqlite3` was already modified before the session. It was neither
    changed nor staged. The tests run on pytest's own test database.

## 2026-10-11 — Account Security Center Phase 4: password reset confirmation and completion

### Prompts
Phase 4 ran across three agent sessions. Prompt text is verbatim; times
are local (UTC−5).

*Session 1 — 2026-10-08, 13:53, began after `/clear`:*

1. @prd/account-security.md @plans/account-security.md

   Implement Phase 4 only: Password Reset Confirmation and Completion.

   Follow the approved PRD and tracer-bullet implementation plan.

   Replace Phase 3's temporary reset-link holding page with Django's
   built-in PasswordResetConfirmView and implement the complete
   password-reset flow.

   Requirements:
   - A valid reset link opens a DaisyUI-styled form to enter and confirm a
     new password.
   - Apply Django's standard password validation.
   - Invalid, expired, and previously used links must be rejected safely.
   - Reset links must expire after one hour, using the existing
     PASSWORD_RESET_TIMEOUT setting.
   - After successfully resetting a password, show a completion page with a
     link to sign in.
   - Do not automatically sign the user in.
   - Send a password-changed notification through the existing console
     email backend after a successful reset.
   - Maintain safe error handling and do not expose account information.
   - Preserve existing functionality from Phases 1–3.

   Create automated tests covering the relevant Phase 4 acceptance
   criteria, including valid and invalid tokens, expiration, password
   validation, successful completion, notification emails, and prevention
   of token reuse.

   Run the complete pytest suite, Ruff checks, Django system checks, and
   migration checks.

   Review the Phase 4 acceptance criteria and explain exactly how I can
   manually verify the feature in the browser.

   Do not implement Phases 5–7. Do not commit
2. The Django server crashed with a SyntaxError in accounts/models.py at
   line 56: Non-UTF-8 code starting with '\x97'.

   Please inspect and fix any encoding corruption introduced during Phase
   4. Check the affected Python files for invalid characters or encoding
   problems.

   Run Django system checks, pytest, and Ruff checks after fixing it.

   Preserve db.sqlite3 and my local test accounts. Do not commit anything
   or begin Phase 5.

*Session 2 — 2026-10-09, 09:39:*

3. Phase 4 manual testing revealed an issue.

   The password-reset email is generated correctly, but opening the link
   displays "Invalid reset link" instead of "Choose a new password."

   The Django server logs show a 301 redirect for the reset URL followed by
   a 200 response on the invalid-link page.

   Please investigate why the freshly generated reset token is rejected.
   Check URL formatting, possible copied line breaks or email
   quoted-printable encoding, Django token validation, and any relevant
   Phase 4 view or routing issues.

   Add a regression test if you find an application bug.

   Run pytest, Ruff, and Django checks after any changes. Preserve
   db.sqlite3 and my local accounts.

   Do not commit anything or start Phase 5. Explain what you find and how I
   should retest.

*Session 3 — 2026-10-11, 21:18:*

4. resume
5. Do not commit Phase 4 or start Phase 5 yet.

   The original issue from manual testing is still unresolved: a freshly
   generated password-reset email link opened the "Invalid reset link"
   page.

   Please specifically investigate the link formatting and token handling.
   The Django console email displayed a long URL split across lines,
   including a trailing "=" character, and the browser/server showed a 301
   redirect before displaying the invalid-link page.

   Check whether the email's quoted-printable transfer encoding or a copied
   line break caused the problem, versus an actual application bug.

   Add a regression test that verifies a link extracted from the generated
   email works end-to-end.

   Keep the login-page success redirect because it follows the PRD. Run the
   full test suite and checks after any fixes.

   Preserve db.sqlite3 and my test accounts. Do not commit until I manually
   verify the reset flow.
6. Phase 4 manual browser testing is complete and passed.

   I verified:
   - A valid reset link opens the new-password form.
   - Weak passwords are rejected.
   - A strong new password successfully resets the account.
   - The user is redirected to the login page.
   - The new password works and the old password is rejected.
   - The password-changed notification appears in the Django console.
   - The previously used reset link displays "Invalid reset link."

   Please update PROMPTS.md with the Phase 4 session history, including
   the exact prompts, implementation summary, automated tests, manual
   testing, encoding issue, quoted-printable email URL issue, regression
   tests, and corrections.

   Run final pytest, Ruff, Django system checks, and migration checks.

   Review git status and stage only the intended Phase 4 files and
   PROMPTS.md. Preserve my modified db.sqlite3 and local test accounts.

   Show me the staged file list, test results, and any deviations from the
   PRD before committing.

   Do not commit anything or start Phase 5 until I approve.
7. I approve the Phase 4 implementation and the 10 staged files.

   Before committing, please add the final CRLF-to-LF correction from this
   session to the Sideways section of the Phase 4 PROMPTS.md entry, so the
   documentation is complete.

   Stage the updated PROMPTS.md and verify that only the 10 intended Phase
   4 files are staged.

   Then commit with the message "Complete the password reset flow" and
   include your Claude co-author line.

   Do not stage or commit db.sqlite3. Preserve my local test accounts.

   After committing, show me the commit hash and final git status. Do not
   begin Phase 5 yet.

### Summary
- **Outcome:** Phase 4 of `plans/account-security.md` is built, manually
  verified by the developer, approved, and committed as "Complete the
  password reset flow". Nothing from Phases 5–7 was added.
  - **Implementation:**
    - `accounts/models.py` adds `User.send_security_notice(subject,
      template_name, context=None, recipient=None)`. It renders a
      plain-text template and sends it to `recipient`, or else to the
      current email, and returns `False` without sending when there is no
      address. It is called only from views, never from saves or signals.
    - `accounts/forms.py` adds `NewPasswordForm`, Django's
      `SetPasswordForm` with DaisyUI classes. It applies
      `AUTH_PASSWORD_VALIDATORS` and checks that the two entries match.
    - `accounts/views.py`:
      - `PasswordResetHoldingView` is removed.
      - `PasswordResetSetView` subclasses `PasswordResetConfirmView`, with
        `post_reset_login = False`. On success it adds the flash message
        "Your password has been reset successfully. Please sign in with
        your new password.", sends the password-changed notice, and
        redirects to `accounts:login`. Django's own token rules handle
        expiry, single use, invalidation by a later password change, and
        sign-out of every existing session. Django also moves the token out
        of the address bar to `/accounts/reset/<uid>/set-password/`.
      - `PasswordResetFinishedView` is a `RedirectView` to login at
        `accounts:password_reset_complete`. It keeps the plan's named URL.
      - `send_password_changed_notice(request, user)` sends the notice with
        the local date and time and an absolute link to
        `accounts:password_reset`. Phase 5 can reuse it.
    - `accounts/urls.py` points `password_reset_confirm` at the new view and
      adds `reset/done/` as `password_reset_complete`.
    - Templates: a new `password_reset_confirm.html` shows "Choose a new
      password" with the form, or "Invalid reset link" with a link to
      request a new one. A new `emails/password_changed_notice.txt` holds
      the date, the time, and the reset-page link, with no password, uid,
      or token. `password_reset_holding.html` is deleted.
  - **Automated verification:**
    - **`accounts/test_password_reset_confirm.py`** is new, with 32 tests:
      - **The form:** a link from the email opens the form, and the token
        is kept out of the address bar.
      - **Rejected passwords:** too short, common or all numbers, too like
        the account, and mismatched entries all show field errors, leave
        the password unchanged, and send no email. A rejected attempt
        leaves the link usable.
      - **Success:** the user lands on login with the exact message and is
        not signed in. The `reset/done/` URL leads on to login. The new
        password works and the old one doesn't. A session signed in on
        another client is sent to login.
      - **The link as delivered:** see the quoted-printable item under
        **Sideways**.
      - **Dead links:** a used link, including a second attempt from a new
        client, plus tampered tokens, unknown uids, and posting to the form
        without opening the link all show the invalid page.
      - **Expiry:** with a 60-second timeout, a link still works at 59
        seconds and fails at 61. With the default timeout it fails after
        one hour. A link issued before a later password change is invalid.
      - **The notice:** exactly one plain-text email, from
        `DEFAULT_FROM_EMAIL`, to the user's address. It has the date and
        the reset link, and contains no password, uid, or token. A user
        with no email gets nothing.
      - **`send_security_notice`:** it sends nothing without an address,
        defaults to the current email, and accepts an explicit recipient.
      - **Silent changes:** `set_password()` + `save()`, the Django admin,
        and `seed` send nothing.
    - **`accounts/test_password_reset.py`:** the holding-page tests are
      removed. The Phase 3 request and settings tests are unchanged.

    The final full suite passes (405 tests). `ruff check`,
    `ruff format --check`, `manage.py check`, `makemigrations --check`, and
    `migrate --check` are clean. Phase 4 adds no migrations.
  - **Manual testing:** the developer tested in the browser and verified:
    - a valid reset link opens the new-password form
    - weak passwords are rejected
    - a strong new password resets the account
    - the user is redirected to the login page
    - the new password works and the old one is rejected
    - the password-changed notice appears in the Django console
    - the used reset link shows "Invalid reset link"
  - **Commit scope:** staged `accounts/forms.py`, `accounts/models.py`,
    `accounts/views.py`, `accounts/urls.py`,
    `accounts/test_password_reset.py`, the new
    `accounts/test_password_reset_confirm.py`,
    `templates/accounts/password_reset_confirm.html`,
    `templates/accounts/emails/password_changed_notice.txt`, the deletion
    of `templates/accounts/password_reset_holding.html`, and `PROMPTS.md`.
    `db.sqlite3` (already modified by the developer's local test accounts)
    was left unstaged and unmodified. The diagnostics and tests used
    pytest's temporary database. One read-only probe in session 3 rendered
    a reset email against the dev database.
- **Deviations:**
  - Prompt 1 asked for "a completion page with a link to sign in". The PRD
    and plan say a successful reset goes to the login page with the
    success message. Session 1 built the completion page and flagged the
    difference. At the start of session 3, the agent read the PRD as
    authoritative and switched to the login redirect before the developer
    had ruled. Prompt 5 then confirmed it ("Keep the login-page success
    redirect because it follows the PRD"). The completion page template was
    deleted.
  - The PRD lists "reset complete" among the views that subclass Django's
    built-ins. Because the confirm step now goes straight to login, it is a
    plain `RedirectView` that only keeps the named URL alive.
  - Prompt 3 asked for a regression test only "if you find an application
    bug". Session 2 found none and added none. Prompt 5 asked for one
    anyway, and session 3 added two.
- **Sideways:**
  - **Encoding corruption (prompt 2):** in session 1, the agent edited
    `accounts/models.py` with an inline Python script that saved in the
    Windows default encoding. The two em dashes in the
    `send_security_notice` docstring became the byte `\x97`, which is not
    valid UTF-8. The same script switched five files to CRLF line endings.
    Ruff refused to read the file, so the agent repaired both problems
    before running the tests. But the developer's dev server reloaded
    while the bad file was on disk and crashed with the `SyntaxError`.
    The Phase 4 summary never mentioned the repair. In session 1's reply
    to prompt 2, the agent confirmed every Phase 4 file was valid UTF-8
    with LF endings, found no `\x97` bytes anywhere in the project,
    admitted it should have reported the repair, and switched to the file
    tools for edits. This entry was written with the file tools for the
    same reason.
  - **Quoted-printable reset link (prompts 3 and 5):** the reset email
    was correct, but the copied link was broken. At host `127.0.0.1:8000`
    the link line is about 81 characters. Python's email library, which
    Django 6 uses, sends any body over 78 characters per line as
    quoted-printable. The console backend prints the raw encoded email, so
    the link appears with a soft break: an `=` at the end of the line, and
    the token's last characters on the next line. Copying only the first
    line gives a URL with no trailing slash and a cut-off token ending in
    `=`. Django's `APPEND_SLASH` answers with a 301, and the token check
    then shows "Invalid reset link". Joining the two lines with the `=`
    kept is also invalid. The decoded link, which a real mail client
    shows, opens the form. The earlier tests missed this because they
    read `message.body`, the text before encoding, at the short
    `testserver` host.
    - Session 2 diagnosed this with a throwaway test, changed no code, and
      explained how to join the lines when retesting.
    - In session 3, after prompt 4 ("resume"), the agent did not have
      session 2's transcript in context and investigated again from
      scratch. It reproduced the same three outcomes, again with no
      application bug.
    - Two regression tests were added at host `127.0.0.1:8000`.
      `test_a_link_read_from_the_delivered_email_resets_the_password`
      decodes the encoded email the way a mail client does, follows the
      link with no 301, sets a new password, lands on login with the
      message, and signs in. `test_a_long_link_is_wrapped_on_the_wire`
      pins the quoted-printable wrapping, so the console's `=` keeps an
      explanation.
    - No application code changed for this. A dev-only email backend
      that prints decoded bodies was offered but not built, because
      `CLAUDE.md` says `EMAIL_BACKEND` is always the console backend.
  - **Line endings (session 3):** the agent repeated a slip from session
    1. It edited `accounts/views.py` and
    `accounts/test_password_reset_confirm.py` with inline Python scripts
    whose `write_text` call saves Windows CRLF line endings. The encoding
    stayed valid UTF-8, and no text changed. The final pre-staging scan
    caught the CRLF endings, and both files were converted back to LF to
    match the other Phase 4 files before staging. Git's
    `core.autocrlf=true` would have stored LF anyway. The agent reported
    this in its staging summary but had left it out of the first version
    of this entry. Prompt 7 asked for it to be added.
  - Writing this entry: session 3 recovered the exact text of prompts 1–3
    from the earlier sessions' local transcripts rather than
    reconstructing it.

## 2026-10-08 — Account Security Center Phase 3: password reset request and email

### Prompts
The session began after `/clear`. Prompt text is verbatim.

1. @prd/account-security.md @plans/account-security.md Implement Phase 3
   only: Password Reset Request and Email.

   Follow the approved PRD and tracer-bullet implementation plan.

   Add the "Forgot password?" link to the login page, the password-reset
   request form, the generic confirmation page, and Django's console-based
   password-reset email.

   Configure PASSWORD_RESET_TIMEOUT with a default of 3600 seconds and
   DEFAULT_FROM_EMAIL through environs.

   The reset email should include a one-hour expiration notice and a working
   link to the minimal holding page specified in Phase 3. The holding page
   must safely recognize valid and invalid links without allowing password
   changes yet.

   Protect customer privacy by showing the same confirmation message whether
   or not an email belongs to an account.

   Use Django's built-in password reset framework and existing DaisyUI
   styling. Do not implement Phase 4's complete password-reset functionality
   or any later phases.

   Run pytest, Ruff lint and formatting checks, and Django migration checks.
   Review each Phase 3 acceptance criterion and explain how I can manually
   test the request and email flow in the browser.

   Do not commit changes yet. Preserve db.sqlite3 and my existing test
   accounts. I want to review and verify this phase before committing.
2. Phase 3 manual testing passed. I verified the Forgot Password form,
   generic confirmation message, console reset email, valid reset-link
   holding page, and identical confirmation for an unregistered email.

   Please append this implementation session to PROMPTS.md under today's
   date, recording every prompt and summarizing the implementation, testing,
   corrections, and results.

   Run final pytest, Ruff, and migration checks. Review git status and stage
   only the intended Phase 3 files and PROMPTS.md. Do not stage or modify
   db.sqlite3.

   Show me the staged file list and test results before committing. Do not
   start Phase 4 yet.

### Summary
- **Outcome:** Phase 3 of `plans/account-security.md` is built and staged,
  and is waiting for the developer's approval before it is committed.
  Nothing from Phases 4–7 was added.
  - **Implementation:**
    - `config/settings.py` reads `DEFAULT_FROM_EMAIL` (default
      `ThoughtTronix <no-reply@thoughttronix.example>`) and
      `PASSWORD_RESET_TIMEOUT` (default `3600`) through environs.
      `EMAIL_BACKEND` stays on the console backend. `.env.example` lists
      both settings, commented out.
    - `accounts/forms.py` adds `PasswordResetRequestForm`, which is Django's
      `PasswordResetForm` with DaisyUI classes. The stock form already
      matches emails case-insensitively and skips inactive accounts and
      accounts without a usable password, so no matching logic was added.
    - `accounts/views.py`:
      - `PasswordResetRequestView` subclasses Django's `PasswordResetView`
        and uses the plain-text email and subject templates in
        `templates/accounts/emails/`. It passes the link lifetime into the
        email from a small `reset_link_lifetime()` helper (3600 → "one
        hour"), so the wording stays true if the timeout is changed.
      - `PasswordResetSentView` subclasses `PasswordResetDoneView`.
      - `PasswordResetHoldingView` is the temporary page at
        `accounts:password_reset_confirm`. It is GET-only (a POST gets 405),
        has no form, uses `never_cache`, and checks the uid and token with
        `default_token_generator.check_token`, which never uses the link up.
    - `accounts/urls.py` adds `password-reset/`, `password-reset/sent/`, and
      `reset/<uidb64>/<token>/`, named as in the plan.
    - Templates:
      - a "Forgot password?" link below the sign-in button on `login.html`
      - new `password_reset_form.html`, `password_reset_done.html` (the
        exact generic message), and `password_reset_holding.html` ("Reset
        link recognized", or "Link not valid" with a link to request a new
        one)
      - new `emails/password_reset_email.txt` and
        `emails/password_reset_subject.txt`
    - `CLAUDE.md` mentions the two new settings.
  - **Automated verification:** 25 new tests in
    `accounts/test_password_reset.py` cover:
    - the login-page link
    - the redirect to the sent page and its exact message
    - an identical page for a registered, an unregistered, and a
      differently capitalized email, with an email-less account present
    - exactly one email for an active account, including a mixed-case match
    - no email for unregistered, inactive, unusable-password, or email-less
      accounts
    - a plain-text email from `DEFAULT_FROM_EMAIL` that says "expires in
      one hour", with wording that follows the timeout setting and a link
      that matches `password_reset_confirm`
    - the email templates' folder
    - valid, tampered-token, and unknown-uid holding pages
    - the link still validating after two visits
    - a POST returning 405 with the password unchanged
    - the settings' `.env` values and defaults, by reloading the settings
      module with `.env` loading turned off
    - the console email backend

    The full suite passes (378 tests). `ruff check`, `ruff format --check`,
    `manage.py check`, `makemigrations --check`, and `migrate --check` are
    clean. Phase 3 adds no migrations.
  - **Manual testing:** the developer tested in the browser and verified:
    - the Forgot Password form
    - the generic confirmation message
    - the reset email printed on the console
    - the holding page for a valid reset link
    - the identical confirmation for an unregistered email
  - **Commit scope:** staged `.env.example`, `CLAUDE.md`,
    `config/settings.py`, `accounts/forms.py`, `accounts/views.py`,
    `accounts/urls.py`, `accounts/test_password_reset.py`,
    `templates/accounts/login.html`, the three new reset page templates, the
    two `templates/accounts/emails/` templates, and `PROMPTS.md`.
    `db.sqlite3` (already modified by the developer's local test accounts)
    was left unstaged and unmodified. The agent only read it to list users
    for the manual-test instructions, and the test suite uses its own
    temporary database.
- **Deviations:** None from a recommended answer, and no follow-up
  questions. Prompt 1 asked for a one-hour expiry notice. The agent derived
  the wording from `PASSWORD_RESET_TIMEOUT` rather than hard-coding "one
  hour", so it reads "one hour" at the default.
- **Sideways:**
  - The first version of the "identical response" test also sent a
    non-email value and a blank value. Both fail form validation and never
    reach the generic redirect, so the agent replaced them with an
    email-less account present alongside the three email cases, plus a
    separate no-email-sent test.
  - Comparing the sent pages byte for byte failed because `base.html` puts a
    CSRF token in `hx-headers`, and Django re-masks it on every render. The
    test now strips that token before comparing.
  - The holding-page "no form" check first tried to slice out `<main>`.
    Signed-out pages have no forms at all (the navbar's logout form is
    signed-in only), so the check became a plain "no `<form`" assertion.
  - The reset email says the link "works only once", as the PRD specifies.
    That only becomes true in Phase 4; the agent pointed this out in its
    Phase 3 review.
  - Writing this entry: the first attempt to insert it through an inline
    shell heredoc failed on quoting, so it was written to a scratch file and
    inserted from there.

## 2026-10-08 — Account Security Center Phase 2: security overview page

### Prompts
The session began after `/clear`. Prompt text is verbatim.

1. I approve the staged files. Please commit Phase 1 with the message
   "Require a unique lowercase email at signup." Do not include db.sqlite3.
   Show me the commit hash when finished, and do not start Phase 2 yet.
2. @prd/account-security.md @plans/account-security.md Implement Phase 2
   only: Security Overview Page.

   Follow the approved PRD and tracer-bullet implementation plan.

   Create the Account Security overview page using DaisyUI cards, display
   the current user's email or the no-email notice, and add the Security
   link to the authenticated navbar next to Addresses.

   Make sure the page requires authentication and works for customers,
   employees, and administrators.

   Do not implement anything from Phases 3–7.

   After implementation, run the automated tests, Ruff checks, and
   migration checks. Review Phase 2's acceptance criteria and explain how I
   can manually verify everything in the browser.

   Do not commit anything yet. I want to review and test Phase 2 myself
   first. Preserve my modified db.sqlite3 and local test accounts.
3. Phase 2 manual browser testing is complete. The Security page displays
   correctly for the employee account, and the authentication redirect
   works.

   Please append this implementation session to PROMPTS.md under today's
   date, including every prompt, the implementation summary, automated
   tests, and manual verification.

   Then review git status, stage only the intended Phase 2 files and
   PROMPTS.md, and preserve db.sqlite3 and my local test accounts.

   Show me the staged files and test results before committing. Do not
   commit or begin Phase 3 until I approve.

### Summary
- **Outcome:** Phase 2 of `plans/account-security.md` is built and staged,
  and is waiting for the developer's approval before it is committed.
  Nothing from Phases 3–7 was added.
  - **Implementation:**
    - `SecurityView` in `accounts/views.py` is a `LoginRequiredMixin` +
      `TemplateView` with no role checks. Customers, staff, and the admin
      all get the same page.
    - `accounts/urls.py` routes `security/` to `accounts:security`
      (`/accounts/security/`).
    - New `templates/accounts/security.html` extends `base.html`. It has one
      DaisyUI **Email** card that shows the address on file, or, when the
      email is blank, the exact notice "No email address on file. Add an
      email address to enable password recovery." in a warning alert.
    - `templates/base.html` gains a "Security" link right after "Addresses",
      inside the signed-in block only.
    - The page has only the Email card. The Password card, the "Change
      email" button, and the Devices card belong to Phases 5, 6, and 7, so
      no button links to a page that doesn't exist yet.
  - **Automated verification:** 10 new tests in `accounts/test_security.py`
    cover:
    - a signed-out visitor is redirected to
      `/accounts/login/?next=/accounts/security/`
    - a customer, a staff member, and an admin each get a 200 response with
      `accounts/security.html`
    - the Email card shows a customer's address and omits the notice
    - the exact no-email notice for a customer, staff, and an admin with
      blank emails
    - the navbar link appears after "Addresses" when signed in and is absent
      when signed out

    The full suite passes (353 tests). `ruff check`, `ruff format --check`,
    `makemigrations --check`, `migrate --check`, and `manage.py check` are
    clean. Phase 2 adds no migrations.
  - **Manual testing:** the developer tested in the browser. The Security
    page displayed correctly for the employee account, and visiting it
    signed out redirected to the login page.
  - **Commit scope:** staged `accounts/views.py`, `accounts/urls.py`,
    `accounts/test_security.py`, `templates/accounts/security.html`,
    `templates/base.html`, and `PROMPTS.md`. `db.sqlite3` (modified by the
    developer's local test accounts) was left unstaged and untouched; the
    test suite runs against its own temporary database.
- **Deviations:** None from a recommended answer. The PRD describes three
  cards on the finished page; following the plan's phase split, this phase
  ships only the Email card.
- **Sideways:**
  - Prompt 1 asked for the Phase 1 commit, but it already existed as
    `eb7de87` from before `/clear`, and nothing was staged. The agent made no
    duplicate commit and reported the existing hash. That commit also
    includes `PROMPTS.md` and the two `.claude/skills/` files, which the
    Phase 1 log had suggested committing separately; the agent offered a
    follow-up split rather than rewriting history.
  - No test or lint failures during implementation.

## 2026-10-08 — Account Security Center Phase 1: email identity at signup

### Prompts
The session began after `/clear`. It spans two transcripts: prompt 1 is in
the first, and prompts 2–4 are in the second, which opened with "resume".
Prompt text is verbatim.

1. @prd/account-security.md @plans/account-security.md Implement Phase 1
   only: Email identity at signup.

   Follow the PRD and the approved tracer-bullet plan exactly. Do not
   implement later phases.

   Before making changes, review the existing authentication code and
   relevant migrations.

   After implementation, run the automated tests and Ruff checks, verify
   the Phase 1 acceptance criteria, and explain how I can manually test the
   feature in my browser.

   Do not commit the changes yet. I want to review and verify Phase 1
   myself first.
2. resume
3. My manual signup and duplicate-email tests passed. Please verify that my
   new account's email was saved in lowercase and review the final Phase 1
   acceptance criteria.

   Check git status and identify which files should be included in the
   Phase 1 commit. Do not modify or restore db.sqlite3, and do not commit
   anything yet.
4. Append a Phase 1 implementation session log to PROMPTS.md under today's
   date, October 8, 2026, with the newest entry at the top.

   Record every prompt I gave you during this implementation session, in
   order, including corrections and follow-up requests.

   Summarize the implementation, automated verification, manual signup
   testing, duplicate-email rejection, and confirmation that the email was
   saved in lowercase.

   Do not modify or commit any other files yet.

### Summary
- **Outcome:** Phase 1 of `plans/account-security.md` is built and not
  committed. Nothing from Phases 2–7 was added.
  - **Implementation:**
    - `User.save()` lowercases the email on every save, so signup, the admin,
      the shell, `create_user`, and `seed` all store it the same way.
    - A conditional `UniqueConstraint(Lower("email"), condition=~Q(email=""))`
      makes emails unique in any capitalization while allowing any number of
      blank emails. Its `violation_error_message` makes the admin show a
      friendly error instead of crashing on a duplicate.
    - Hand-written data migration `0003_lowercase_emails` lowercases existing
      emails. If it finds case-insensitive duplicates, it stops with a
      `RuntimeError` naming each address and its usernames.
      `0004_unique_lowercase_email` adds the constraint only after that.
    - `SignupForm` asks for username, email, password, and confirmation, in
      that order, with email required. `clean_email` lowercases the address
      and puts "A user with that email address already exists." on the email
      field for a duplicate in any capitalization.
    - `CLAUDE.md` points to the new PRD and plan and describes the email
      rules.
  - **Automated verification:** 15 new tests in
    `accounts/test_email_identity.py` cover:
    - signup field order, required email, and lowercasing
    - duplicate rejection in two capitalizations
    - the database constraint (using `bulk_create`, which skips `save()`)
    - several blank emails
    - lowercasing and duplicate rejection in the admin and `create_user`
    - sign-in for staff without an email
    - `seed`
    - both migration paths, run from `0002` forward

    The two existing signup tests in `accounts/tests.py` now post an email.
    The full suite passes (343 tests). `ruff check`, `ruff format --check`,
    and `makemigrations --check` are clean. In the second transcript, the
    agent re-ran these checks and mapped each of the nine acceptance
    criteria to its test.
  - **Manual testing:** the agent did not migrate the committed
    `db.sqlite3`; it ran both migrations against a scratch copy, where all 13
    users came through correctly. The developer then migrated `db.sqlite3`
    and tested in the browser. Signing up as `dana` with a mixed-case email
    worked. A second signup reusing that email in different capitalization
    was rejected with the email-field error. The agent confirmed in the
    database that the new account `dana` is stored with
    `dana@example.com`, that no account was created by the rejected attempt
    (14 users, only one `dana*`), and that no user has a mixed-case email.
  - **Commit scope:**
    - Recommended for the Phase 1 commit: the `accounts/` model, form, test
      and migration changes, `CLAUDE.md`, `prd/account-security.md`, and
      `plans/account-security.md`.
    - Left to the developer: `PROMPTS.md`, and the two new
      `.claude/skills/` directories (suggested as a separate commit).
    - Left out: `db.sqlite3`, changed by the developer's migration and manual
      signup, is the grading snapshot and was neither modified nor restored
      by the agent.
- **Deviations:** None from a recommended answer. Prompt 1 asked for no
  commit, and prompt 3 asked again for no commit and for `db.sqlite3` not to
  be modified or restored; both were followed. The developer migrated the
  database themselves, using the browser-test steps the agent gave.
- **Sideways:**
  - No test or lint failures during implementation.
  - The session was split by "resume", so the second transcript rebuilt
    state from git and the plan, then re-ran the full suite before reporting.
  - For this log: the agent read the first transcript to recover prompt 1.
    Its extraction script hit a Windows `cp1252` encoding error twice. The
    second retry failed because `python -I` ignores `PYTHONIOENCODING`.
    Calling `sys.stdout.reconfigure(encoding="utf-8")` in the script fixed it.

## 2026-10-08 — Account Security Center: tracer-bullet plan (no implementation)

### Prompts
The session began after `/clear`. Prompt text is verbatim.

1. /prd-to-plan @prd/account-security.md
2. Before creating the final implementation plan, present the proposed
   tracer-bullet phases and their corresponding user stories. Stop and wait
   for my explicit approval. Do not implement any code or automatically
   approve the phase breakdown.
3. I want changes before approving. Please revise the breakdown as follows:

   1. Email identity at signup — stories 1–7.
   2. Security overview page — stories 8, 9, 12–14.
   3. Password reset request and email — the login link, request form,
      generic confirmation, console reset email, and one-hour expiry.
   4. Password reset confirmation and completion — valid and expired links,
      new password submission, redirect to login, and password-changed
      notification.
   5. Change password — stories 10 and 21–26.
   6. Change email — stories 15–20.
   7. Sign out of all other devices — stories 11 and 37–42.

   Redistribute stories 27–36, 43–44, and 46–47 between Phases 3 and 4
   based on their actual requirements.

   Incorporate story 45 and all seed, admin, and documentation checks into
   the phases where those behaviors are introduced. Do not create a
   separate cleanup phase.

   Ensure every phase has complete, independently verifiable functionality
   and that all 47 user stories are covered.

   Show me the revised seven-phase breakdown for approval. Do not write the
   final plan or implement any code yet.
4. I approve the revised seven-phase breakdown, with one adjustment to
   Phase 3.

   Please make Phase 3 independently verifiable by including a minimal
   working destination for the password-reset link rather than leaving an
   unresolved URL. It should safely recognize the link without allowing a
   password change yet, and clearly explain that the completion step
   belongs to Phase 4.

   Phase 4 should then implement the complete password-reset confirmation
   flow, including password validation, successful completion, expired and
   used-token handling, session invalidation, and security notification.

   Keep all 47 user stories covered, preserve the seven phases, and include
   clear acceptance criteria for each phase.

   You may now write the final tracer-bullet implementation plan to
   plans/account-security.md.

   Do not implement any application code yet.
5. We have finished comparing the naive plan with the tracer-bullet plan.
   The tracer-bullet plan provides smaller, independently verifiable
   phases, integrates testing earlier, and avoids separate preparation and
   cleanup phases.

   Please delete only the old account-security-draft.md file from the
   parent directory. Keep prd/account-security.md and
   plans/account-security.md unchanged. Do not modify any application code.
6. Append a session log to PROMPTS.md at the repository root under today's
   date, October 8, 2026, newest entry at the top.

   Record every prompt I gave you during this planning session in
   chronological order, including my requests to revise the phase
   breakdown, split password-reset functionality, integrate seed and
   documentation checks, and add a minimal working reset-link destination.

   End with a short summary explaining the outcome, how the naive and
   tracer-bullet plans differed, the corrections I requested, and anything
   that went sideways.

   Do not modify the PRD, implementation plan, or application code.

### Summary
- **Outcome:** `plans/account-security.md` was written: seven
  tracer-bullet phases covering all 47 PRD stories, each with
  "What to build" and acceptance criteria. The phases are email identity,
  the Security page, the reset request, reset confirmation, change
  password, change email, and sign out of other devices. A header fixes
  the URL paths and names, the model and migration decisions, the auth
  approach, the notification rules, and the settings. The old naive draft,
  `../account-security-draft.md`, was deleted. The PRD and application
  code were not touched, and `CLAUDE.md` is not updated yet; the plan
  assigns that to Phases 1, 3 and 7.
- **Naive vs tracer-bullet:** The naive draft (written before this
  session) opened with a "Phase 0 — Prep" for settings and test fixtures
  and ended with separate seed and docs work, in the style of the earlier
  feature plans. The tracer-bullet plan has no prep or cleanup phase: each
  setting, fixture, seed check and `CLAUDE.md` update arrives in the phase
  whose behavior needs it, and every phase ends with tests that show it
  working on its own.
- **Deviations:** My first breakdown had seven phases, with a combined
  reset phase and a final "Seed, admin and docs" phase. I asked for the
  reset work to be split into a request phase and a confirm phase, with
  the stories redistributed between them, and for story 45 and every
  seed, admin and docs check to move into the phase that introduces the
  behavior. For the reset link in Phase 3, Claude recommended only
  registering the confirm URL name so the email could build the link.
  I instead asked for a minimal holding page that recognizes the link,
  allows no password change, and is fully replaced in Phase 4.
- **Sideways:** Claude's first reply already presented the breakdown and
  waited, so my second prompt got the same breakdown again, now with a
  story-coverage table. The split I asked for created a real gap: the
  Phase 3 reset email linked to a confirm page that would not exist until
  Phase 4. Claude flagged it before writing the plan, and the holding page
  closed it. The PRD left the exact URL paths and names open, so Claude
  chose them and asked me to review them before Phase 1. The deleted
  draft was outside the repo, so the deletion cannot be undone through
  git; Claude read its opening first to confirm it was the right file.
  The naive and tracer-bullet plans were compared outside the session;
  Claude only read the draft's first lines.

## 2026-10-08 — Account Security Center: grill interview and PRD (no implementation)

### Prompts
Bracketed labels name the question an answer settled; the prompt text is
verbatim.

1. /grill-me I want to design an Account Security Center for ThoughtTronix.
   Customers should be required to provide an email address when signing
   up, be able to change their passwords while signed in, and reset
   forgotten passwords through email. I also want a dedicated account
   security page where customers can view and manage their security
   settings.

   Please interview me to clarify the requirements, recommend one or two
   additional useful security features, and help me make design decisions.
   Do not implement anything or create a PRD or plan yet.
    Copy prompt
2. [Q1] I choose **Option A**. Email addresses should be required and
   unique for every customer account, but customers should continue signing
   in with their usernames.

   I also agree that email uniqueness should be case-insensitive, so
   addresses with different capitalization are treated as the same email.
   Normalize email addresses to lowercase when saving them and enforce
   case-insensitive uniqueness.

   I want to preserve the existing authentication system as much as
   possible while improving account security. Let's continue to the next
   design question. Do not implement anything or create the PRD yet.
3. [Q2] I choose **Option B**. I want email uniqueness enforced through both
   form validation and a database constraint that excludes blank emails.

   Email addresses should be normalized to lowercase, and uniqueness should
   be case-insensitive across all account creation and update methods.

   Customer signup must require an email, but existing staff and
   administrator accounts may have blank emails to preserve compatibility.

   Before implementing the database constraint, check for existing
   duplicate emails and account for them safely in the migration plan.

   Let's continue to the next design question. Do not implement anything or
   create the PRD or plan yet.
4. [Q3] I choose Option A. Let's subclass Django's built-in password
   management views and use custom templates and DaisyUI-styled forms so
   the Account Security Center stays consistent with ThoughtTronix.

   I want to use Django's built-in password validation, hashing, password
   reset tokens, and session security instead of recreating these features.

   Keep all authentication URLs under the existing accounts namespace,
   preserve the current username-based login system, and provide clear
   success and error messages for customers.

   Continue with the next design question. Do not implement anything or
   create the PRD or implementation plan yet.
5. [Q4] I choose **Option A**. The password-reset process should always
   display the same confirmation message, regardless of whether the email
   address is registered.

   Use a message such as: "If an account exists with that email address,
   we've sent password-reset instructions. Please check your inbox and spam
   folder."

   I want to prevent account enumeration and protect customer privacy while
   keeping the implementation consistent with Django's built-in
   authentication framework.

   For now, let's leave rate limiting as a potential future enhancement
   rather than adding it to the current scope.

   Continue with the next design question. Do not implement anything or
   create the PRD or plan yet.
6. [Q5] I choose **Option B**, with a security notification sent to the
   customer's previous email address.

   Customers should be able to update their email address from the Account
   Security Center, but they must enter their current password to authorize
   the change.

   The new email must be required, normalized to lowercase, and validated
   for case-insensitive uniqueness.

   After a successful update, display a confirmation message and send a
   notification to the previous email address informing the customer that
   their account email was changed. The notification should not contain
   passwords or other sensitive information.

   Use Django's existing console email backend for development. We can
   leave email verification with confirmation links as a future
   enhancement.

   Continue with the next design question. Do not implement anything or
   create the PRD or plan yet.
7. [Q6] I choose **Options A and B** as the two additional security
   features.

   For Option A, send a security notification whenever a customer's
   password changes, including changes made through the password-change
   form and successful password resets. The notification should include the
   date and a link to the password-reset page without exposing sensitive
   information. Use the existing console email backend.

   For Option B, add a "Sign out of all other devices" button to the
   Account Security Center. Require the customer's current password before
   performing the action, terminate their other active sessions, and
   preserve their current session.

   Please plan this feature using Django's existing session and
   authentication mechanisms rather than introducing unnecessary
   dependencies. Include automated tests verifying that other sessions are
   invalidated while the current one remains active.

   Leave recent sign-in activity and two-factor authentication out of scope
   for now.

   Continue with the next design question. Do not implement anything or
   create the PRD or plan yet.
8. [Q7] I choose **Option A**. Add a per-user session salt to the custom
   User model and incorporate it into Django's session authentication hash.

   When customers select "Sign out of all other devices," require their
   current password, generate a new session salt, invalidate other
   sessions, and preserve the current session using Django's session
   authentication mechanisms.

   Make sure this works correctly with password changes and resets without
   modifying the customer's actual password.

   Include automated tests using two separate authenticated sessions to
   confirm that the current session remains active while the other session
   is invalidated on its next request.

   Keep the implementation compatible with Django's authentication system
   and avoid introducing unnecessary dependencies.

   Continue with the next design question. Do not implement anything or
   create the PRD or implementation plan yet.
9. [Q8] I choose **Option A**. The Account Security Center should be
   accessible to every authenticated user, including customers, employees,
   and administrators.

   Use one consistent security page protected by Django's
   LoginRequiredMixin. All authenticated users should be able to change
   their passwords, update their email addresses, and sign out of other
   devices.

   For staff or administrator accounts without an email address, display a
   message such as "No email address on file. Add an email address to
   enable password recovery."

   The Forgot password link should appear on the login page for everyone.
   If an account does not have an email or the submitted address is not
   recognized, use the same generic confirmation message to prevent account
   enumeration.

   Preserve the existing staff and administrator permissions. Accessing the
   Account Security Center should not change anyone's role or permissions.

   Continue with the next design question. Do not implement anything or
   create the PRD or plan yet.
10. [Q9] I choose **Option A**. Create a dedicated Account Security overview
    page with separate pages for changing email, changing password, and
    signing out of other devices.

    The overview page should display the customer's current email address,
    password management option, and device/session security option using
    DaisyUI cards.

    Each action should open its own form page. After successful completion,
    redirect the user to the Security overview page and display a clear
    confirmation message using Django's messages framework.

    Add a "Security" link to the authenticated navbar next to "Addresses."
    Include a link back to the Security Center after a successful password
    change, and keep the password-reset email linked directly to the reset
    flow for signed-out users.

    Follow the existing ThoughtTronix template conventions, extend
    base.html, and avoid unnecessary JavaScript or HTMX complexity.

    Continue with the next design question. Do not implement anything or
    create the PRD or plan yet.
11. [Q10] I choose **Option A**. After a successful password reset,
    redirect the customer to the login page with a success message such as
    "Your password has been reset successfully. Please sign in with your new
    password."

    Do not automatically sign customers in after resetting their passwords.
    Keep the behavior consistent with ThoughtTronix's existing signup and
    login process.

    I also agree with setting PASSWORD_RESET_TIMEOUT to 3600 seconds (1
    hour), configurable through .env using environs, with 3600 as the
    default.

    The password-reset email should clearly state that the link expires in
    one hour. Reset links should become invalid after successful use or
    another password change.

    Continue with the next design question if any requirements remain
    unresolved. Do not implement anything or create the PRD or plan yet.
12. [Q11] I choose **Option A**, and I approve all the proposed defaults.

    Security notification emails should be triggered explicitly from the
    successful self-service password-change, password-reset, and
    email-change flows.

    Keep the reusable email notification logic in a method on the User
    model, following the existing project architecture and keeping the
    views thin. Do not create a new accounts/services.py module.

    Password changes made through the Django admin, shell, or seed command
    should not trigger notifications.

    I approve plain-text email templates in templates/accounts/emails/,
    using DEFAULT_FROM_EMAIL configured through .env with the proposed
    default.

    I also approve the standard Django password-change form, the signup
    email field positioned between username and password, and the proposed
    out-of-scope list: rate limiting, email verification, recent sign-in
    activity, two-factor authentication, and login lockout.

    Make sure notifications are triggered only after successful changes and
    that accounts without an email address are handled gracefully.

    If there are no more unresolved design questions, summarize our final
    decisions and confirm that the /grill-me interview is complete. Do not
    create the PRD or implementation plan yet.
13. /to-prd
14. Before moving on, review the entire prd/account-security.md against all
    11 decisions from our /grill-me interview.

    Verify that every agreed requirement is represented, all user stories
    are consistent with those decisions, and the Out of Scope section
    contains the features we intentionally excluded.

    Identify any missing, contradictory, or unapproved requirements. If
    corrections are necessary, explain them and update the PRD.

    Do not implement anything or create an implementation plan yet.
15. Please check the final saved version of prd/account-security.md and
    confirm that the Out of Scope section has no duplicate entries or
    contradictory requirements. Fix any remaining duplicates.

    Do not implement anything or create an implementation plan yet.
16. Append a session log to PROMPTS.md at the repo root, under today's
    date, newest entry at the top. Record every prompt I gave you this
    session, in order, including any corrections. End the entry with a
    short summary: the outcome, any places where I deviated from a
    recommended answer or asked follow-up questions, and anything that went
    sideways.

### Summary
- **Outcome:** An 11-question grill interview settled the design, recorded
  in `prd/account-security.md` (47 user stories):
  - signup requires an email; it is lowercased on every save and unique
    regardless of capitalization, enforced by the forms and by a database
    constraint that skips blank emails (staff and admin may stay blank);
    login stays username-based
  - the migration lowercases emails and stops with a list of any
    duplicates before adding the constraint (the dev database had none)
  - thin subclasses of Django's password-change and password-reset views
    under `accounts:`; the forgot-password form always gives the same
    reply; reset links last one hour (`PASSWORD_RESET_TIMEOUT` from
    `.env`) and lead to the login page without signing in
  - email change with the current password and a notice to the old address
  - two extra features: a password-changed notice, and "Sign out of all
    other devices" through a per-user `session_salt` mixed into the session
    hash
  - one Security overview page for every signed-in user, with a separate
    page per action and a navbar link
  - notices are sent only from the three self-service flows, through a
    `User` method, as plain-text templates; no fourth deep module

  Only the PRD was written. There is no plan or implementation yet, and
  `CLAUDE.md` does not list the PRD yet; that waits until the plan exists.
- **Deviations:** Every recommended option was accepted. Additions beyond
  the recommendations: the duplicate check in the migration (Q2), the exact
  reset and no-email messages (Q4, Q8), the two-session test requirement
  (Q6, Q7), and the link back to the Security Center after a password
  change (Q9). Rate limiting, email verification, sign-in activity and
  two-factor authentication were explicitly deferred. Follow-ups after the
  PRD: a review against all 11 decisions, then a check of Out of Scope for
  duplicates.
- **Sideways:** The first prompt arrived with a stray "Copy prompt" from
  the clipboard; it was ignored. The review found four problems in the
  first PRD draft: "trims" emails (never approved); "no automatic sign-in
  after signup" (never discussed); a `docs/TESTING.md` path in a section
  the template keeps free of paths; and an Out of Scope list that mixed
  explicitly deferred features with exclusions implied by other decisions.
  All four were fixed. The final check found no duplicates and changed
  nothing. Writing this log, the first attempt failed because a shell
  heredoc could not parse the entry; nothing was written, and the entry
  went in through a scratch file instead.

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
