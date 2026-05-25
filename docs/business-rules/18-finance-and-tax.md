# Finance & Tax Rules

## Purpose

Help property owners submit rental income documentation to a **Chartered Accountant (CA)** for tax filing.

## Models

### `CAProfile`

- One-to-one with `User`
- `firm_name`, `contact_email`, `phone`, `verified`

### `TaxSubmissionToCA`

- `user` — property owner
- `ca` — optional FK to `CAProfile`
- `financial_year` — e.g. `2024-25`
- `sent_to_email`, `sent_at`, `message`

## API rules

| Endpoint | Access |
|----------|--------|
| `CAProfileViewSet` | Authenticated (queryset is global — consider scoping) |
| `TaxSubmissionToCAViewSet` | Filtered by `tax_summary__user` (requires related model) |
| `GET /finance/download-tax-files/?fy=2024-25` | Authenticated owner |

## Download tax package rules

1. Query param `fy` defaults to `2024-25`.
2. Collects all `Unit` objects for `request.user`.
3. Generates Excel + PDF via `finance.utils`.
4. Bundles renter `rent_agreement` and `police_verification` files if present.
5. Returns ZIP attachment `tax_documents.zip`.

## Subscription link

`UserSubscription.tax_reminder_days_before` (default 7) — days before tax due to remind (used by reminder jobs when enabled).

## Related files

- `finance/models.py`
- `finance/views.py`
- `finance/utils.py`
- `management/commands/send_tax_reminders.py`

## See also

- [Owner reporting](./12-owner-reporting.md)
