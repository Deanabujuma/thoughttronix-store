# PRD: The ThoughtTronix Store — Account Security Center

*Settled in a design interview on 2026-10-08. Extends `prd/core-platform.md`; where the two disagree, this document wins for account security only.*

---

## Problem Statement

A ThoughtTronix customer signs up with only a username and a password. The store never learns their email address, so when they forget their password there is no way back into the account — they have to ask staff or create a new account and lose their order history and saved addresses. Once signed in, they also can't change their password, can't see or update the contact details tied to their account, and can't do anything if they left themselves signed in on a shared or lost device. Nothing tells them when something important about their account changes, so a takeover would go unnoticed.

## Solution

Every new customer gives an email address at signup, and that address is unique to their account. Customers keep signing in with their username exactly as they do today.

A new **Security** page, linked from the navbar, gathers everything about protecting the account in one place:

- **Email** — shows the address on file and lets the customer change it after confirming their current password. The old address is told about the change.
- **Password** — lets the customer change their password by entering the current one and a new one twice.
- **Devices** — a "Sign out of all other devices" action that, after confirming the current password, ends every other session while keeping the current one signed in.

A **Forgot password?** link on the login page lets anyone request a reset link by email. The page always gives the same answer whether or not the address is registered, so it can't be used to discover who shops at ThoughtTronix. The link works once and expires after one hour; after resetting, the customer signs in with their new password.

Whenever a customer's password or email changes through these self-service flows, the store emails them a short security notice so an unexpected change doesn't go unnoticed.

Staff and the administrator use the same Security page; it doesn't change anyone's role or permissions.

## User Stories

### Signup and email identity

1. As a new customer, I want to provide my email address when I sign up, so that I can recover my account if I forget my password.
2. As a new customer, I want signup to reject an email address that another account already uses, so that each email belongs to exactly one account.
3. As a new customer, I want `Dana@Example.com` and `dana@example.com` treated as the same address, so that capitalization can't create a confusing second account for my inbox.
4. As a new customer, I want to keep signing in with my username, so that signing in works the way the store already does.
5. As a returning customer, I want my existing username and password to keep working unchanged, so that this feature doesn't disrupt my account.
6. As a store administrator, I want existing staff and admin accounts without an email to keep working, so that adding the email requirement doesn't lock anyone out.
7. As a store administrator, I want email uniqueness enforced no matter how an account is created or edited (signup, Django admin, shell, seed), so that password reset can always rely on one email meaning one account.

### Security overview page

8. As a signed-in customer, I want a "Security" link in the navbar, so that I can find my security settings easily.
9. As a signed-in customer, I want a Security page that shows my current email address, so that I can confirm where account emails go.
10. As a signed-in customer, I want the Security page to offer changing my password, so that I can manage it from one place.
11. As a signed-in customer, I want the Security page to offer signing out of other devices, so that I can secure my account after using a shared computer.
12. As a staff member or administrator with no email on file, I want the Security page to tell me "No email address on file. Add an email address to enable password recovery.", so that I know password recovery isn't available to me yet.
13. As a signed-out visitor, I want the Security page to send me to sign in, so that no one can see or change account settings without being signed in.
14. As a staff member or administrator, I want to use the same Security page as customers, so that I can protect my more privileged account with the same tools.

### Changing email

15. As a signed-in customer, I want to change my email address from the Security page, so that my account stays reachable when my email changes.
16. As a signed-in customer, I want to enter my current password to authorize an email change, so that someone using my unattended signed-in session can't redirect my account email.
17. As a signed-in customer, I want the new email checked with the same rules as signup (required, case-insensitive unique), so that the change can't create a duplicate or an empty address.
18. As a signed-in customer, I want a clear confirmation message after changing my email, so that I know the change took effect.
19. As a customer, I want a notice sent to my previous email address when my account email changes, so that I find out if someone else changed it.
20. As a staff member with no previous email, I want to add an email without anything going wrong, so that I can turn on password recovery.

### Changing password

21. As a signed-in customer, I want to change my password by entering my current password and my new password twice, so that only I can change it and I don't mistype it.
22. As a signed-in customer, I want my new password checked against the store's password rules, so that I can't choose a weak password.
23. As a signed-in customer, I want to stay signed in on this device after changing my password, so that I don't have to sign in again immediately.
24. As a signed-in customer, I want changing my password to sign out my other devices, so that anyone using my old password elsewhere loses access.
25. As a signed-in customer, I want a confirmation message and to return to the Security page after changing my password, so that I know it worked and can continue managing my security.
26. As a customer, I want an email notice when my password changes, including the date and a link to reset my password, so that I can act quickly if I didn't make the change.

### Forgotten password

27. As a signed-out customer, I want a "Forgot password?" link on the login page, so that I can recover my account.
28. As a signed-out customer, I want to request a reset link by entering my email address, so that I can recover my account without contacting staff.
29. As a customer, I want the reset request to always show "If an account exists with that email address, we've sent password-reset instructions. Please check your inbox and spam folder.", so that attackers can't use the form to discover who has an account.
30. As a customer, I want the reset email to state that the link expires in one hour, so that I know to use it promptly.
31. As a customer, I want the reset link to stop working after one hour, after I use it, or after my password changes another way, so that an old or leaked link can't be used to take over my account.
32. As a customer following an expired or already-used link, I want a clear message telling me the link is invalid and how to request a new one, so that I'm not stuck.
33. As a customer, I want my new password checked against the store's password rules during reset, so that recovery doesn't allow a weak password.
34. As a customer who just reset my password, I want to be sent to the login page with "Your password has been reset successfully. Please sign in with your new password.", so that I can confirm my new password works.
35. As a customer, I want resetting my password to sign out all my existing sessions, so that anyone already in my account loses access.
36. As a customer, I want an email notice after a successful reset, so that I know if someone else reset my password.

### Signing out other devices

37. As a signed-in customer, I want a "Sign out of all other devices" action, so that I can end sessions on devices I no longer control without changing my password.
38. As a signed-in customer, I want to enter my current password to confirm signing out other devices, so that someone using my unattended session can't lock me out of my other devices.
39. As a signed-in customer, I want to stay signed in on the device I used, so that securing my account doesn't sign me out too.
40. As a signed-in customer, I want my other devices signed out on their next page load, so that the action takes effect right away.
41. As a signed-in customer, I want signing out other devices to leave my password unchanged and send no password-change notice, so that the action does only what it says.
42. As a signed-in customer, I want a confirmation message after signing out other devices, so that I know it worked.

### Notifications and operations

43. As a customer, I want security notices to contain no passwords, reset links that grant access, or other sensitive details, so that a forwarded or intercepted notice can't be used against me.
44. As a customer, I want security notices sent only after a change actually succeeds, so that failed attempts don't produce misleading emails.
45. As a developer, I want password changes made through the Django admin, shell, or `seed` command to send no notices, so that resetting the demo world doesn't flood the console.
46. As a developer, I want all emails to keep using the console backend in development, so that I can read reset links and notices without a mail server.
47. As a developer, I want the sender address and reset-link lifetime configurable through `.env` with working defaults, so that the app still runs with no `.env` present.

## Implementation Decisions

### Email identity (accounts app, `User` model)

- `User` keeps `AbstractUser`'s optional `email` field; email stays blank-allowed at the model level so existing staff/admin accounts without one remain valid. Required-ness is a rule of customer signup and of the email-change form.
- The model lowercases the email on every save, so normalization covers signup, the email-change form, the Django admin, the shell, and the seed alike.
- Uniqueness is case-insensitive and enforced twice:
  - **Forms:** signup and email-change forms reject an address that matches another account case-insensitively, with a friendly field error.
  - **Database:** a `UniqueConstraint` on the lowercased email, conditioned to exclude blank emails (the same conditional-constraint pattern `Address` uses for its defaults).
- Signup login remains username-based; no custom authentication backend.

### Migrations

- A data migration lowercases every existing email, then checks for case-insensitive duplicates among non-blank emails and **stops with a clear error listing them** rather than choosing which account keeps an address. The constraint is added only after that check. (At the time of the interview, the development database had 13 users, no duplicates, no mixed-case emails, and one blank email.)
- A new per-user `session_salt` field is added with a callable random default, so every existing user receives their own distinct value rather than one shared value.

### Session invalidation ("Sign out of all other devices")

- `User` overrides `get_session_auth_hash()` to mix `session_salt` into Django's normal password-based session hash.
- A model method on `User` (e.g. "sign out other sessions") rotates the salt and saves it; the view then refreshes the current session with Django's `update_session_auth_hash`, so the current session survives and every other session fails Django's hash check on its next request.
- Rotating the salt never touches the password hash, so it never triggers a password-change notice and never invalidates outstanding reset links on its own. Password changes and resets continue to sign out other sessions through Django's built-in mechanism.
- Works with any session backend; no scanning or deleting `django_session` rows, no session-tracking table.

### Views and URLs (accounts app, `accounts:` namespace)

- Thin class-based views subclassing Django's built-ins, matching the existing `SignInView`/`SignOutView` style: password change, password-reset request, reset "sent", reset confirm, and reset complete. Each sets its template, DaisyUI-styled form, namespaced success URL, and flash message.
- New views: the Security overview, the email-change form, and the sign-out-other-devices confirmation form.
- Every view except the reset flow requires sign-in via `LoginRequiredMixin`. All authenticated users — customers, staff, admin — have access; no role checks are added or changed.
- Every new URL is named under `accounts:`.
- Success flows:
  - Change email → Security overview with a confirmation message.
  - Change password → Security overview with a confirmation message.
  - Sign out other devices → Security overview with a confirmation message.
  - Reset request → the generic "If an account exists…" page, whatever was entered.
  - Reset confirm → login page with "Your password has been reset successfully. Please sign in with your new password." No automatic sign-in after reset.
- An invalid, expired, or used reset link shows a clear message with a link to request a new one.

### Forms

- **Signup:** Django's `UserCreationForm` plus a required email field placed between username and password. The form's docstring no longer says "No email."
- **Change password:** Django's standard password-change form (current, new, confirm), styled with DaisyUI classes; new passwords pass `AUTH_PASSWORD_VALIDATORS`.
- **Reset request / set new password:** Django's built-in reset forms, styled with DaisyUI. The reset request form matches emails case-insensitively and skips inactive accounts and accounts without a usable password, while the page response stays identical.
- **Change email:** new email (required, normalized, case-insensitively unique excluding the user's own account) plus the current password, which the form verifies.
- **Sign out other devices:** current password only, verified by the form.

### Notifications

- One reusable method on `User` (e.g. `send_security_notice`) renders a plain-text email template with context and sends it, defaulting to the user's current email and accepting an explicit recipient. It does nothing when there is no address.
- Called explicitly from views only after success:
  - Password change → notice to the current email (date and a link to the password-reset page).
  - Password reset confirm → the same password-changed notice.
  - Email change → notice to the *previous* email; skipped when the previous email was blank.
- Not triggered by model saves, `set_password`, or signals, so the Django admin, shell, `createsuperuser`, and `seed` send nothing.
- Notices contain no passwords, tokens, or other sensitive data.
- No new service module: the project's three deliberate deep modules stay as they are.

### Settings

- `PASSWORD_RESET_TIMEOUT` read from `.env` via environs, default `3600` (one hour).
- `DEFAULT_FROM_EMAIL` read from `.env` via environs, default `ThoughtTronix <no-reply@thoughttronix.example>`.
- `EMAIL_BACKEND` stays the console backend.

### Templates

- All pages extend `base.html` and use Tailwind + DaisyUI classes only; no HTMX or JavaScript.
- Security overview: three DaisyUI cards — **Email** (current address or the no-email notice, "Change email" button), **Password** ("Change password" button), **Devices** ("Sign out of all other devices" button).
- One form page each for change email, change password, and sign out other devices; reset request, sent, confirm, and complete pages.
- Plain-text email templates for the reset email (states the one-hour expiry), the password-changed notice, and the email-changed notice, kept together in an `emails` folder under the accounts templates.
- Navbar: a "Security" link for signed-in users next to "Addresses". Login page: a "Forgot password?" link for everyone.

### Testing

- Follows the project's testing conventions. Key behaviors to cover:
  - Signup requires email; rejects case-insensitive duplicates; stores lowercase.
  - The database constraint rejects case-insensitive duplicates but allows multiple blank emails.
  - Reset request shows the identical page and message for registered, unregistered, and email-less accounts; sends mail only for a registered active account.
  - Reset links work once, expire after the configured timeout, and die after a password change; a successful reset redirects to login without signing in and sends the notice.
  - Password change keeps the current session, signs out others, and sends the notice; a failed attempt sends nothing.
  - Email change requires the correct current password, enforces uniqueness, and notifies only the previous address (none when it was blank).
  - Sign out other devices: two separately signed-in clients; after one confirms, it stays signed in while the other is redirected to login on its next request; the password is unchanged and no notice is sent.
  - Security pages redirect signed-out visitors to login and work for customers, staff, and admin alike.
  - The seed sends no email.

## Out of Scope

Deferred as future enhancements (explicitly excluded in the interview):

- Rate limiting of password-reset requests.
- Verifying a new email address with a confirmation link before it takes effect.
- Recent sign-in activity / login history.
- Two-factor authentication.
- Login lockout after failed attempts.

Excluded by other decisions in this PRD:

- Signing in with an email address — login stays username-only (Q1).
- Real email delivery (SMTP or a provider) — the console backend remains (Q5, Q11).
- Automatic sign-in after a password reset — the customer signs in on the login page (Q10).
- Notifications for changes made through the Django admin, shell, `createsuperuser`, or `seed` (Q11).
- HTMX inline forms on the Security page — each action has its own page (Q9).

## Further Notes

- Django's reset view emails a link for every active account matching the address; the case-insensitive unique constraint guarantees that is at most one.
- An account with a blank email cannot receive a reset email; the generic response still hides that fact. Such accounts see the no-email notice on their Security page and can add an address there.
- The seed already assigns every demo user a lowercase email, so it stays compatible with the constraint and the reset flow can be demonstrated with seeded customers.
- Because email is now how accounts are recovered, the email-change flow is the most sensitive form on the site; the current-password check and the old-address notice are its safeguards until verification links are added.
