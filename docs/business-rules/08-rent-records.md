# Rent Record Rules

## Model

`properties.models.RentRecord` — one payment obligation per renter per month.

## Business rules

1. **Relations:** must link `renter`, `unit`, and `owner`; `renter.unit` must equal `unit`.
2. **Uniqueness:** one record per (`renter`, `rent_month`) — `rent_month` is first day of month (e.g. `2025-05-01`).
3. **`amount_paid`:** cannot be negative.
4. **`date_paid`:** cannot be before `rent_month`.
5. **Payment status:** `PENDING`, `PAID`, `FAILED`.
6. **On create:**
   - Razorpay payment link generated (`create_payment_link`)
   - WhatsApp sent to renter with link
   - `rent_records` feature usage incremented
7. **Payout fields:** `payout_status`, `payout_reference`, retry counters, `razorpay_order_id`, `razorpay_payment_status`.
8. **Invoice:** `invoice_number`, `invoice_pdf` after payment/receipt generation.
9. **Late fee:** `late_fee`, `grace_days`, `rent_due_date`, `rent_due_day` — see `apply_late_fee_if_needed()` in utils.

## Computed properties (for integrations)

- `amount` → `amount_paid`
- `due_date` → `rent_due_date`
- `month` / `year` → from `rent_month`

## API

| Method | Path |
|--------|------|
| GET/POST | `/api/rent-records/` |
| GET | `/api/rent-records/{id}/invoice/` |

## Post-payment (intended)

When `payment_status == PAID` (signals, if wired):

- Cancel reminder job
- Thank-you voice note
- In-app notification
- Email receipt

## Related files

- `properties/models/rent_record_models.py`
- `properties/views/rent_record_views.py`
- `properties/serializers/rent_record_serializers.py`
- `rentsecure_be/services/razorpay_service.py`

## See also

- [Payments & webhooks](./16-payments-and-webhooks.md)
- [Payout retry](./11-payout-retry.md)
