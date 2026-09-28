# PRD: The ThoughtTronix Store — Discount Codes

*Settled in a design interview on 2026-09-28. Extends `prd/core-platform.md`; where the two disagree, this document wins for discount codes only.*

---

## Problem Statement

Marketing wants to run promotions, and the store has no way to take a discount. `place_order` has carried a dormant `coupon_code` seam since the core platform shipped; nothing behind it exists.

## Requirements

- Customers can enter discount codes at checkout.
- Expired codes need a clear error message.
- Marketing can create and retire codes without changing past orders.
- Codes can discount either the whole order or specific products.

## Decisions

### The code

| # | Decision |
|---|----------|
| Q1, Q12 | **Percentage only**, whole numbers **1–99**. No code can make an order free, so checkout never needs a no-payment path. |
| Q3, Q4 | **Applies to** is an explicit choice: *Whole order* or *Selected products*. Selected products are hand-picked (many-to-many to `Product`). The form requires at least one product for *Selected products* and rejects any for *Whole order*. |
| Q5 | Validity is a **required expiry date** plus an **Active** switch. Retiring = switching Active off (reversible). |
| Q6 | A code is valid **through** its expiry date: expired when `localdate() > expires_on`. |
| Q7 | `TIME_ZONE = "America/Chicago"` project-wide — one clock for coupons, the dashboard, and order timestamps. |
| Q9 | Codes are trimmed and **uppercased** on save and on lookup; **unique forever** (a retired name is never reused); 3–30 letters, digits, or hyphens. |
| Q16 | `Coupon` lives in the `orders` app. Code says "coupon"; people see "Discount code". |

### Money

| # | Decision |
|---|----------|
| Q2 | Only **eligible lines** are discounted; **every unit** on an eligible line counts. A product code with no eligible product in the cart is an error, never a silent $0.00. |
| Q11 | Each eligible line (`unit_price × quantity`) is discounted and rounded **half-up to the cent**; the order discount is the **sum of the line discounts**, so the two always agree. |
| Q10 | Snapshot: `Order` gets `discount_code`, `discount_percent`, `discount_amount`, and a nullable **PROTECT** link to the coupon; `OrderItem` gets its own `discount_amount`. A used code can be retired, never deleted. |
| Q13 | `Order.total` is **the amount paid**. `Order.subtotal` is a property: `total + discount_amount`. Existing orders need no data migration. The dashboard's top-products revenue subtracts line discounts. |
| Q20 | **One code per order.** The customer applies one code at a time; a failed Apply clears the code; nothing is ever applied automatically. |

### Checkout

| # | Decision |
|---|----------|
| Q14 | The code field sits on the checkout page with an HTMX **Apply** button that previews the discounted order summary. The code travels only as a form field — nothing is stored on the cart — and `place_order` re-validates it. |
| Q15 | One validator, `Coupon.objects.redeem(code, cart)`, raises `InvalidCouponError` (a `ValueError`). The preview, `CouponForm.clean_coupon_code`, and `place_order` all call it. *(Amended during build: the interview named `CheckoutForm.clean_coupon_code`, but `prd/core-platform.md` forbids `clean_*` methods on `CheckoutForm`, so the code field gets its own small form, validated in the same POST.)* A failure in `place_order` lands beside the code field. `CheckoutView` also catches the generic `ValueError` from `place_order` and returns the customer to the cart. |
| Q8 | Messages, checked in this order: **unknown** → *"We don't recognize the code BOGUS."* · **retired** → *"THOUGHTS10 is no longer available."* · **expired** → *"THOUGHTS10 expired on Sep 30, 2026."* · **no eligible product** → *"HUB10 applies to Seraphine, which isn't in your cart."* Product lists shorten after three names ("… and 4 more"). |

### After purchase

| # | Decision |
|---|----------|
| Q19 | Both order-detail pages share one `_order_lines.html` partial showing each line's discount beneath its line total, plus a subtotal / discount / total block. The confirmation says what the customer saved. Lists (history, staff orders) show only the amount paid. Undiscounted orders look exactly as before. The staff detail links the code to its back-office page. |

### The back office

| # | Decision |
|---|----------|
| Q17 | After a code's first use its **terms lock**: code, percent, applies-to, and products become read-only. Expiry date and Active stay editable. |
| Q18 | A **Discount codes** tab: code, percent, applies to, valid through, status, uses; filter tabs *All / Live / Expired / Retired*; 20 per page. Status precedence matches the customer messages: Retired, then Expired, then Live. Uses count every order, cancelled included. Delete appears only on unused codes; used codes get Retire. Designed empty states for "no codes yet" and "no codes with that status". |

### Seed and tests

| # | Decision |
|---|----------|
| Q21 | The seed creates `THOUGHTS10` (live, whole order), `HUB15` (live, Seraphine products), `SUMMER20` (expired), and `LAUNCH25` (retired), and some seeded orders use them. Coupon choices draw from their own RNG so the existing orders are unchanged. `conftest.py` gains `whole_order_coupon`, `product_coupon`, `expired_coupon`, `retired_coupon`, dated relative to `timezone.localdate()`. |

## Out of Scope

Fixed-amount codes, stacking, free orders, start dates, per-customer or usage limits, automatic best-code selection, category- or tag-scoped codes.
