# Payout Retry Rules

## Flow

1. Renter pays rent → `payment_status = PAID`
2. System triggers Cashfree payout to owner’s registered bank
3. `payout_status` → `SUCCESS` or `FAILED`
4. Owner may **retry** failed payouts via API

## Retry API rules

**Endpoint:** `POST /api/owner/retry_payout_api/<rent_id>/`

| Rule | Value |
|------|--------|
| Authentication | Owner JWT required |
| Ownership | `RentRecord.owner == request.user` |
| Payment | `payment_status == "PAID"` |
| Payout | `payout_status == "FAILED"` |
| Action | Calls `process_rent_payout(rent)` |
| On success | `send_payout_notification(rent)` |

## Owner bank prerequisites

- `OwnerBankDetails` with verified `beneficiary_id` (Cashfree)
- Updated via `POST /api/api/owner/update-bank-details/`

## Webhook

`POST /api/webhook/cashfree/payout/` updates status from `transferId` → `payout_reference`.

## Notification rules

- Owner WhatsApp expected in **international format** (e.g. `+91...`) on `UserProfile.whatsapp_number`
- Payout success/failure messages via `notification.services.rent_notify_service`

## Known code issues

- Some paths use `rent.renter.property.owner` — model uses **`unit`**, not `property`
- `cashfree_service.pay_owner_after_rent` references fields that may not exist on all models

## Related files

- `properties/views/rent_record_views.py` (`retry_payout_api`)
- `rentsecure_be/services/cashfree_service.py`
- `core/views.py` (`cashfree_payout_webhook`, `update_owner_bank_details`)

## See also

- [Payments & webhooks](./16-payments-and-webhooks.md)
- [Rent records](./08-rent-records.md)
