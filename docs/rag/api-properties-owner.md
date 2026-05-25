# RAG-009 — API: Properties (Owner)

**Metadata:** `id=RAG-009` | `tags=buildings,units,renters,rent-records,api` | `app=properties`

## Base paths

- `/api/` (primary)
- `/properties/` (duplicate router)

All require **JWT** unless noted.

## ViewSet resources (router)

| Resource | Path | ViewSet |
|----------|------|---------|
| Buildings | `/api/buildings/` | `BuildingViewSet` |
| Units | `/api/units/` | `UnitViewSet` |
| Caretakers | `/api/caretakers/` | `CaretakerViewSet` |
| Renters | `/api/renters/` | `RenterViewSet` |
| Rent records | `/api/rent-records/` | `RentRecordViewSet` |
| Extra charges | `/api/extra-charges/` | `ExtraChargeViewSet` |
| Unit images | `/api/unit-images/` | `UnitImageViewSet` |
| Unit documents | `/api/unit-all-documents/` | `UnitDocumentViewSet` |
| Rent agreements | `/api/rent-agreements/` | `RentAgreementDraftViewSet` |

## Custom owner endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/owner/rent-records/` | List owner's rent records |
| GET | `/api/owner/rents/` | Rent overview list |
| GET | `/api/owner/dashboard-summary/` | Metrics, trends, defaulters |
| POST | `/api/owner/retry_payout_api/<rent_id>/` | Retry failed Cashfree payout |
| GET | `/api/rent-records/<id>/invoice/` | Download invoice PDF |

## Leegality

| Method | Path |
|--------|------|
| POST | `/api/leegality/webhook/` |

## Create side effects

- **Building/Unit/Renter/etc.:** `FeatureEnforcer.can_create()` + `increment()`
- **Rent record create:** Razorpay link + WhatsApp to renter (`rent_record_views.py`)

## Default renter list filter

`RenterViewSet` queryset: `status in ["active", "notice_period"]` only.

## Code layout

- Views: `properties/views/*.py`
- Serializers: `properties/serializers/`
- Limits: `properties/feature_enforcer.py`
