# Plan: The ThoughtTronix Store — Account Security Center

> Source PRD: `prd/account-security.md`

*The PRD owns the decisions; this plan owns the sequence. Each phase is a thin vertical slice through model, migration, form, view, template, and tests, and the suite is green at every phase boundary.*

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning app**: `accounts`. No new app, and no new service module. The project's three deliberate deep modules stay as they are.
- **URLs** (all named, under the `accounts:` namespace, mounted at `/accounts/`):

  | Path | Name | Sign-in |
  |---|---|---|
  | `/accounts/security/` | `accounts:security` | required |
  | `/accounts/security/email/` | `accounts:email_change` | required |
  | `/accounts/security/password/` | `accounts:password_change` | required |
  | `/accounts/security/devices/` | `accounts:sign_out_other_devices` | required |
  | `/accounts/password-reset/` | `accounts:password_reset` | none |
  | `/accounts/password-reset/sent/` | `accounts:password_reset_done` | none |
  | `/accounts/reset/<uidb64>/<token>/` | `accounts:password_reset_confirm` | none |
  | `/accounts/reset/done/` | `accounts:password_reset_complete` | none |

- **Models**: `accounts.User` keeps `AbstractUser`'s blank-allowed `email` and lowercases it on every save. A conditional `UniqueConstraint` on the lowercased email excludes blank emails, following the same pattern as `Address`. A new `session_salt` field has a callable random default, so each user gets their own value. `get_session_auth_hash()` mixes in the salt. `send_security_notice` is the single place notices are sent from. There are no new models or relationships.
- **Migrations**: (1) a data migration lowercases emails, then stops with an error that lists any case-insensitive duplicates; (2) the constraint is added only after that; (3) `session_salt` is added with a distinct value per user.
- **Auth and authorization**: sign-in stays username-only, with no custom backend. The Security pages use `LoginRequiredMixin` and are open to every authenticated user: customers, staff, and admin. No role checks are added or changed.
- **Views**: thin class-based views. Where Django has a built-in view (password change and the reset flow), the view subclasses it, matching the `SignInView` / `SignOutView` style.
- **Notifications**: plain-text templates in `templates/accounts/emails/`. They are sent only from views, and only after the change succeeds. Model saves, `set_password`, and signals never send them, so the admin, shell, `createsuperuser`, and `seed` stay silent. Notices never contain passwords or tokens.
- **Settings**: `PASSWORD_RESET_TIMEOUT` (default `3600`) and `DEFAULT_FROM_EMAIL` (default `ThoughtTronix <no-reply@thoughttronix.example>`) are read from `.env` via environs. `EMAIL_BACKEND` stays on the console backend.
- **Templates**: every page extends `base.html` and uses only Tailwind + DaisyUI, with no HTMX or JavaScript.

---

## Phase 1: Email identity at signup

**User stories**: 1, 2, 3, 4, 5, 6, 7

### What to build

Every new customer gives an email at signup, and an email can belong to only one account, regardless of capitalization. The `User` model lowercases email on save, so signup, the admin, the shell, and `seed` all store emails the same way. A data migration lowercases existing emails and refuses to continue if it finds duplicates. After that, the conditional constraint makes uniqueness a database guarantee. The signup form gains a required email field between username and password, with a friendly duplicate error, and its docstring no longer says "No email." Sign-in is unchanged.

### Acceptance criteria

- [ ] Signup shows username, email, password, and confirmation, in that order. Email is required.
- [ ] Signing up with `Dana@Example.com` stores `dana@example.com`.
- [ ] Signup rejects an email that another account already uses in any capitalization, with an error on the email field, and creates no account.
- [ ] The database rejects two users whose emails differ only in capitalization, and accepts several users with blank emails.
- [ ] Saving a user through the Django admin or `User.objects.create_user` stores the email in lowercase.
- [ ] The data migration lowercases mixed-case emails. Given case-insensitive duplicates, it stops with an error naming them and does not add the constraint.
- [ ] Existing users, including staff and admin with a blank email, still sign in with their username and password.
- [ ] `seed` runs cleanly against the constraint, and every seeded user has a lowercase email.
- [ ] `CLAUDE.md` points to `prd/account-security.md` and `plans/account-security.md`, and its `accounts/` description notes the unique, lowercase email.

---

## Phase 2: Security overview page

**User stories**: 8, 9, 12, 13, 14

### What to build

A signed-in user can reach a Security page from the navbar. It shows an **Email** card with the address on file, or, when there is none, the notice "No email address on file. Add an email address to enable password recovery." The page is the home that later phases add their cards to. Signed-out visitors are redirected to sign in.

### Acceptance criteria

- [ ] Signed-in users see a "Security" navbar link next to "Addresses". Signed-out visitors do not.
- [ ] `accounts:security` redirects a signed-out visitor to the login page, with `next` set back to the page.
- [ ] A customer sees their current email on the Email card.
- [ ] A user with a blank email sees the exact no-email notice.
- [ ] A customer, a staff member, and an admin each get a 200 response with the same page.

---

## Phase 3: Password reset request and email

**User stories**: 27, 28, 29, 30, 46, 47

### What to build

A signed-out customer can follow "Forgot password?" from the login page, enter an email, and always see the same generic confirmation. A reset email for a registered, active account appears on the console. The request form matches emails case-insensitively and quietly skips inactive accounts and accounts without a usable password. The reset email is plain text, comes from the configured sender, and says the link expires in one hour. The sender address and link lifetime come from `.env`, with working defaults.

The emailed link opens a **minimal holding page** at `accounts:password_reset_confirm`, so this phase can be verified end to end. That page checks the uid and token without using them up. A valid link gets a message that it was recognized and that setting a new password is still to come (the Phase 4 step). An invalid link gets a message that it is not valid. The holding page has no form and accepts no POST, so no password can change during this phase. Phase 4 replaces it completely.

### Acceptance criteria

- [ ] The login page shows a "Forgot password?" link to `accounts:password_reset`, for every visitor.
- [ ] Submitting the request form redirects to `accounts:password_reset_done`. That page shows exactly: "If an account exists with that email address, we've sent password-reset instructions. Please check your inbox and spam folder."
- [ ] The response is identical for a registered email, an unregistered email, an email in different capitalization, and an account with no email.
- [ ] Exactly one email is sent for a registered, active account (including a mixed-case match). None is sent for unregistered, inactive, or unusable-password accounts.
- [ ] The reset email is plain text, comes from `DEFAULT_FROM_EMAIL`, says the link expires in one hour, and contains a link to `accounts:password_reset_confirm`.
- [ ] The reset email template lives in `templates/accounts/emails/`.
- [ ] Following the emailed link shows the "link recognized" holding page. A tampered token shows the "not valid" message. Neither page offers a way to change the password.
- [ ] After visiting the holding page, the link still validates, so the token has not been used up.
- [ ] A POST to the holding page does not change the password.
- [ ] `PASSWORD_RESET_TIMEOUT` and `DEFAULT_FROM_EMAIL` take their values from `.env` when set, and fall back to `3600` and `ThoughtTronix <no-reply@thoughttronix.example>` when no `.env` is present.
- [ ] `EMAIL_BACKEND` is still the console backend.
- [ ] `CLAUDE.md` mentions the two new `.env` settings.

---

## Phase 4: Password reset confirmation and completion

**User stories**: 31, 32, 33, 34, 35, 36, 43, 44, 45

### What to build

The holding page is replaced by the full reset flow. A valid link opens a DaisyUI-styled set-password form, and new passwords must pass `AUTH_PASSWORD_VALIDATORS`. A successful reset ends every existing session, redirects to the login page with "Your password has been reset successfully. Please sign in with your new password.", and does not sign the user in. A link that has expired, has been used, or was issued before a later password change shows a clear message with a link to request a new one.

This phase also adds `User.send_security_notice`. It renders a plain-text template and sends it to the user's current email by default, or to an explicit recipient, and does nothing when there is no address. The reset view sends the **password-changed notice** (date plus a link to the reset page) only after the reset succeeds. Admin, shell, and `seed` password changes never go through this path.

### Acceptance criteria

- [ ] No holding-page wording is left. A valid link shows a new-password form with confirmation.
- [ ] A weak or mismatched new password is rejected with field errors. The password is unchanged and no email is sent.
- [ ] A successful reset redirects to the login page with the exact success message, and the user is not signed in.
- [ ] The new password works at sign-in, and the old one does not.
- [ ] A session signed in before the reset is redirected to login on its next request.
- [ ] A used link shows the "invalid link" page with a link to `accounts:password_reset`.
- [ ] A link past the configured timeout shows that page too, tested by overriding `PASSWORD_RESET_TIMEOUT`.
- [ ] A link issued before a later password change shows that page too.
- [ ] A successful reset sends exactly one password-changed notice to the user's email. It includes the date and a link to `accounts:password_reset`, and contains no password, uid, or token.
- [ ] `send_security_notice` sends nothing when the user has no email and no recipient is given.
- [ ] Notice templates live in `templates/accounts/emails/`.
- [ ] Changing a password through the Django admin, through `set_password()` + `save()`, or by running `seed` sends no email.

---

## Phase 5: Change password

**User stories**: 10, 21, 22, 23, 24, 25, 26

### What to build

The Security page gains a **Password** card with a "Change password" button. It opens a DaisyUI-styled Django password-change form: current password, then the new password twice. A successful change keeps the current session, signs out every other session through Django's built-in mechanism, returns to the Security page with a confirmation message, and sends the password-changed notice from Phase 4.

### Acceptance criteria

- [ ] The Security page shows a Password card that links to `accounts:password_change`.
- [ ] `accounts:password_change` redirects signed-out visitors to login, and works for customers, staff, and admin.
- [ ] A wrong current password, a mismatched confirmation, or a password that fails the validators gives field errors. The password is unchanged and no email is sent.
- [ ] A successful change redirects to `accounts:security` with a confirmation message.
- [ ] After a change, the client that made it is still signed in, and a second client signed in as the same user is redirected to login on its next request.
- [ ] A successful change sends exactly one password-changed notice to the current email, with the date and a link to the reset page, and no secrets.
- [ ] A user with no email can change their password without error, and no email is sent.

---

## Phase 6: Change email

**User stories**: 15, 16, 17, 18, 19, 20

### What to build

The Email card gains a "Change email" button. It opens a form that takes a new email and the current password. The new email follows the same rules as signup: required, lowercased, and unique in any capitalization, not counting the user's own account. The form checks the current password. On success the user returns to the Security page with a confirmation message, and a notice goes to the **previous** address. No notice is sent if there was no previous address, for example when staff add an email for the first time.

### Acceptance criteria

- [ ] The Email card has a "Change email" button to `accounts:email_change`, and that page redirects signed-out visitors to login.
- [ ] A wrong current password gives an error, and the email is unchanged.
- [ ] A blank email gives an error, and the email is unchanged.
- [ ] An email used by another account in any capitalization gives an error, and the email is unchanged.
- [ ] Re-entering the user's own address in different capitalization is accepted and stored in lowercase.
- [ ] A successful change saves the new lowercase email and redirects to `accounts:security` with a confirmation message. The Email card then shows the new address.
- [ ] A successful change sends exactly one email-changed notice, addressed to the previous email only and containing no secrets.
- [ ] A user with a blank email can add an address. No notice is sent, and the no-email notice disappears.
- [ ] A failed attempt sends no email.
- [ ] Editing a user's email in the Django admin sends no notice.
- [ ] After the change, a password-reset request for the new address sends a reset email, and a request for the old address does not.

---

## Phase 7: Sign out of all other devices

**User stories**: 11, 37, 38, 39, 40, 41, 42

### What to build

`User` gains `session_salt`, which a migration fills with a distinct random value per user. `get_session_auth_hash()` combines the salt with Django's password-based hash. A model method rotates and saves the salt. The Security page gains a **Devices** card with a "Sign out of all other devices" button. It opens a confirmation form that asks only for the current password. On success the view rotates the salt and refreshes the current session with `update_session_auth_hash`. The current device stays signed in, every other session fails Django's hash check on its next request, and the user returns to the Security page with a confirmation message. The password, outstanding reset links, and notices are untouched.

### Acceptance criteria

- [ ] After the migration, every existing user has a non-empty `session_salt`, and no two users share one.
- [ ] The Security page shows a Devices card that links to `accounts:sign_out_other_devices`, which redirects signed-out visitors to login.
- [ ] A wrong current password gives an error, and the other session stays signed in.
- [ ] With two clients signed in as the same user, the one that confirms is redirected to `accounts:security` with a confirmation message and stays signed in.
- [ ] The other client is redirected to login on its next request.
- [ ] The user's password hash is unchanged.
- [ ] No email is sent.
- [ ] A password-reset link issued before the action still works.
- [ ] Customers, staff, and admin can all use it.
- [ ] Users created by `seed`, and users that existed before the migration, still sign in normally.
- [ ] `CLAUDE.md` notes the per-user session salt behind "Sign out of all other devices".

---

## Story coverage

| Phase | Stories |
|---|---|
| 1 | 1, 2, 3, 4, 5, 6, 7 |
| 2 | 8, 9, 12, 13, 14 |
| 3 | 27, 28, 29, 30, 46, 47 |
| 4 | 31, 32, 33, 34, 35, 36, 43, 44, 45 |
| 5 | 10, 21, 22, 23, 24, 25, 26 |
| 6 | 15, 16, 17, 18, 19, 20 |
| 7 | 11, 37, 38, 39, 40, 41, 42 |

All 47 stories are covered. Stories 43 and 44 (no secrets in notices, sent only on success) start in Phase 4 and are tested again for each notice in Phases 5 and 6.
