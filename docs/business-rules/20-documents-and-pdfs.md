# Documents & PDFs Rules

## App: `documents`

Generates PDFs for agreements, receipts, and property dossiers.

## API base

`/documents/document/`

| Endpoint | Purpose |
|----------|---------|
| `rent_receipt/` | Rent receipt PDF |
| `properties/` | Unit dossier PDF |
| `rent_agreement/` | Rent agreement PDF |

All registered as ViewSets on `DefaultRouter`.

## Business rules

1. Generation requires authenticated user (per ViewSet permissions).
2. Templates rendered via Django templates + PDF library (WeasyPrint used in `properties/utils` for invoices).
3. Plan feature `export_pdf_dossier` may gate dossier export (check plan limits where enforced).
4. Rent receipts also generated on payment via `properties/services/receipt_service.py`.

## Overlap with `properties`

- `generate_rent_invoice_pdf` in `properties/utils`
- `ai_assistant.services.invoice_service` — final invoice on renter exit
- `documents` app — dedicated PDF API surface

## Related files

- `documents/views.py`
- `documents/urls.py`
- `properties/services/receipt_service.py`
- `properties/pdf_utils.py`

## See also

- [Rent agreement drafts](./10-rent-agreement-drafts.md)
- [Rent records](./08-rent-records.md)
