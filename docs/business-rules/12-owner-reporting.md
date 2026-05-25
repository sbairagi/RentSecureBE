# Owner Reporting Rules

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/owner/rent-records/` | All rent records for owner |
| `GET /api/owner/rents/` | Simplified rent overview list |
| `GET /api/owner/dashboard-summary/` | Metrics, trends, defaulters |

## Dashboard summary rules

Aggregates **only** `RentRecord` where `owner == request.user`:

1. **Total collected** — sum `amount_paid` where `payment_status == PAID`
2. **This month** — paid records with `rent_month >= first day of current month`
3. **Payouts** — counts by `payout_status` (`SUCCESS`, `PENDING`, `FAILED`)
4. **Trends** — last 6 months paid rent, grouped by month
5. **Defaulters** — `PENDING` or `"UNPAID"` with `rent_due_date < today`

## Assumptions

- Every rent record has valid `owner`, `renter`, and `unit` links
- `amount_paid` is the collected amount field used in aggregates
- Defaulter payload uses `rent.due_date` property (`rent_due_date`)

## Owner rent overview

Returns per record: tenant name, unit, amount, month/year, payment status, payout status, invoice link where applicable.

## Related files

- `properties/views/owner_dashboard.py`
- `properties/views/rent_record_views.py` (`owner_rent_records`, `owner_rent_overview`)

## See also

- [Rent records](./08-rent-records.md)
- [Finance & tax](./18-finance-and-tax.md)
