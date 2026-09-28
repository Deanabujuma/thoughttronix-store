# Implementation Plan: The ThoughtTronix Store — Discount Codes

*Companion to `prd/discount-codes.md`. The PRD owns the decisions; this plan owns the sequence. The suite is green at every phase boundary.*

---

## Phase 0 — Prep

1. `TIME_ZONE = "America/Chicago"`.
2. `CheckoutView.form_valid` catches the `ValueError` from `place_order` and returns the customer to the cart with its message.

**Verification.** The full suite passes under the new timezone; a test covers the caught `ValueError`.

## Phase 1 — Tracer Bullet: One Whole-Order Code, Every Layer

1. `Coupon` model with its queryset (`live`, `expired`, `retired`, `redeem`), `InvalidCouponError`, and the per-line discount math.
2. Snapshot fields on `Order` and `OrderItem`; `Order.subtotal`, `OrderItem.net_total`; `Cart.priced(coupon)`.
3. `place_order` redeems the code and snapshots the discount.
4. A plain discount-code field on checkout, validated by its own `CouponForm` (`CheckoutForm` stays declarative per the core PRD); a failure from `place_order` lands on the field.
5. Confirmation shows the savings; the dashboard's top products subtract line discounts.
6. `Coupon` in the Django admin; coupon fixtures in `conftest.py`.

**Out of bounds:** product scope, the HTMX preview, the back office.

## Phase 2 — Product Scope

Selected-products codes discount only eligible lines; the "no eligible product" error with its shortened product list.

## Phase 3 — The Checkout Preview

HTMX Apply and Remove, the `_order_summary.html` partial, and the place-order button updated out-of-band.

## Phase 4 — After Purchase

The shared `_order_lines.html` partial with per-line discounts and the subtotal / discount / total block on both detail pages.

## Phase 5 — The Back Office

The Discount codes tab: list with status filter and empty states, create and edit with locked terms, Retire, delete for unused codes only; the staff order detail links to the code.

## Phase 6 — Seed and Docs

Demo codes and discounted demo orders; `CLAUDE.md` updated. The `PROMPTS.md` entry is written after review.
