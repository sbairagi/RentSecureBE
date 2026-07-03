# Rent Agreement Draft Rules

## Model

`properties.models.RentAgreementDraft` — e-sign workflow via Leegality.

## Business rules

1. Links **user** (owner), **renter**, and **unit**.
2. **Ownership:** `unit.owner` must be `request.user`.
3. **Consistency:** `renter.unit` must match `unit`.
4. **Limit:** `rent_agreement_drafts` feature key on create (`FeatureEnforcer`).
5. **Leegality:** `leegality_document_id` and webhook update signing status (`POST /api/leegality/webhook/` or `/properties/...`).
6. **Send for signature:** via `rentsecure_be.services.leegality_service` from unit/agreement views.

## API

| Method | Path |
|--------|------|
| GET/POST | `/api/rent-agreements/` |
| POST | `/api/leegality/webhook/` |

## Dashboard (legacy)

- `/dashboard/agreements/` — agreement status view
- `/dashboard/retry-signature/<rent_id>/`

## Related files

- `properties/models/renter_models.py` (`RentAgreementDraft`)
- `properties/views/unit_views.py` (`RentAgreementDraftViewSet`, `leegality_webhook`)
- `rentsecure_be/services/leegality_service.py`
- `smartbot/actions.py` (`send_agreement_for_signature`)

## See also

- [Documents & PDFs](./20-documents-and-pdfs.md)
- [SmartBot](./21-smartbot.md)
