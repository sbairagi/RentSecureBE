# Payments & Webhooks Rules

## Razorpay (rent collection)

### Create payment link

When a `RentRecord` is created:

1. `create_payment_link(rent)` in `rentsecure_be/services/razorpay_service.py`
2. Amount in **paise** (`amount_paid * 100`)
3. Customer: renter name, phone, email
4. Callback URL configured (should match deployed backend)
5. `payment_link` stored on record; WhatsApp sent to renter

### Webhook

**URL:** `POST /api/rent/payment-callback/`

**Active handler (last definition in `core/views.py`):**

- Event: `payment_link.paid`
- Loads rent by `reference_id` from payload
- Sets `payment_status = PAID`
- Calls `process_rent_payout(rent)`

**Note:** An earlier handler verified HMAC signature for `payment.captured` — it is **overwritten** by the later function.

### Manual order creation

`create_rent_payment` POST creates Razorpay **order** and stores `razorpay_order_id` (alternate flow).

## Cashfree (owner payout)

### Registration

- `POST /api/api/owner/update-bank-details/` — saves `OwnerBankDetails`, registers beneficiary

### Payout trigger

After rent marked **PAID**:

- `process_rent_payout(rent)` — requires `beneficiary_id`
- `transfer_id` = `rent_{id}`
- Updates `payout_status`, `payout_reference`

### Webhook

**URL:** `POST /api/webhook/cashfree/payout/`

- Maps `transferId` → `RentRecord.payout_reference`
- `TRANSFER_SUCCESS` / `TRANSFER_FAILED` → updates `payout_status`
- May send WhatsApp via `send_payout_notification`

## Business rules summary

| Step | Rule |
|------|------|
| Collect | Renter pays full rent amount (no partial in link config) |
| Record | `payment_status` must be PAID before payout |
| Payout | Owner must have verified Cashfree beneficiary |
| Retry | Only if payout FAILED and payment PAID |

## Related files

- `rentsecure_be/services/razorpay_service.py`
- `rentsecure_be/services/cashfree_service.py`
- `rentsecure_be/utils/cashfree_payout.py`
- `core/views.py`

## See also

- [Rent records](./08-rent-records.md)
- [Payout retry](./11-payout-retry.md)
