# RAG-013 — Payments: Razorpay & Cashfree

**Metadata:** `id=RAG-013` | `tags=razorpay,cashfree,webhook,payout` | `paths=rentsecure_be/services/,core/views.py`

## Collect rent (Razorpay)

**When:** `RentRecord` created in `RentRecordViewSet.perform_create`

**Service:** `rentsecure_be/services/razorpay_service.py` → `create_payment_link(rent_record)`

- Amount in paise: `amount_paid * 100`
- Stores `payment_link` on record
- WhatsApp sent to renter

**Webhook:** `POST /api/rent/payment-callback/`

- Handler: `razorpay_webhook` in `core/views.py` (**duplicate definitions** — last wins)
- Active handler: `payment_link.paid`, expects `reference_id` = rent id
- **Bug:** payment link creation may not set `reference_id`
- **Security bug:** active handler may lack HMAC verification

On PAID → `process_rent_payout(rent)` in `rentsecure_be/services/cashfree_service.py`

## Pay owner (Cashfree)

**Prerequisite:** `OwnerBankDetails` with `beneficiary_id` via `POST /api/api/owner/update-bank-details/`

**Payout:** `make_payout(transfer_id=f"rent_{id}", amount=rent.amount, bene_id=...)`

**Webhook:** `POST /api/webhook/cashfree/payout/` — updates `payout_status` from `transferId`

**Retry:** `POST /api/owner/retry_payout_api/<rent_id>/` if PAID + payout FAILED

## RentRecord payment fields

- `payment_status`: PENDING | PAID | FAILED
- `payout_status`: PENDING | SUCCESS | FAILED (strings in code)
- `razorpay_order_id`, `payment_link`, `payout_reference`

## Known attribute bugs (AI caution)

Several payout paths use invalid chains:

- `rent.renter.property.owner` — use `rent.owner`
- `owner.profile` — use `userprofile` or `User.whatsapp_number`
- `rent.owner.beneficiary_id` — use `OwnerBankDetails`

See `docs/bugs/rentsecure_be.md`, `docs/bugs/core.md`.
