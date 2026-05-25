# RAG-011 — API: Finance & Documents

**Metadata:** `id=RAG-011` | `tags=finance,tax,pdf,api`

## Finance (`/finance/`)

| Resource | Path | View |
|----------|------|------|
| CA profiles | `/finance/` (router) | `CAProfileViewSet` |
| Tax submissions | `/finance/` (router) | `TaxSubmissionToCAViewSet` |
| Tax ZIP download | GET `/finance/...` | `DownloadTaxFilesView` — query `?fy=2024-25` |

**Models:** `finance/models.py` — `CAProfile`, `TaxSubmissionToCA`

**Known bugs:** `tax_summary__user` filter invalid; `Unit.renter` does not exist — see `docs/bugs/finance.md`.

## Documents (`/documents/`)

Router under `documents/urls.py` → prefix `/documents/document/`:

| Resource | Basename |
|----------|----------|
| Rent receipt PDF | `rent_receipt` |
| Unit dossier PDF | `unit-dossier-pdf` |
| Rent agreement PDF | `rent-agreement-pdf` |

Example pattern: `/documents/document/rent_receipt/` (verify trailing slash).

## Dashboard (`/dashboard/`)

Not in INSTALLED_APPS but URLs exist:

- `/dashboard/agreements/`
- `/dashboard/retry-signature/<rent_id>/`

## Related code

- `finance/utils.py` — Excel/PDF/ZIP generation
- `documents/views.py` — PDF ViewSets
