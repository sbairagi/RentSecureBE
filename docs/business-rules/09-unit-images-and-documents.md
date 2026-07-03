# Unit Images & Documents Rules

## Models

- `properties.models.UnitImage`
- `properties.models.UnitDocument`

## Business rules

1. **Belong to** a `Unit`; may optionally reference a `Renter`.
2. **Ownership:** `unit.owner` must equal `request.user`.
3. **Plan limits:**
   - Images: `max_unit_images` / `unit_images`
   - Documents: `max_document_uploads` / `unit_documents`
4. **Deduplication:** model `clean()` blocks duplicate uploads using **SHA-256 file hash**.
5. **Create:** `FeatureEnforcer` check + increment; cache key `unit_images_user_*` / `unit_docs_user_*` cleared on change.
6. **Destroy:** decrement usage counter.

## API

| Method | Path |
|--------|------|
| GET/POST | `/api/unit-images/` |
| GET/POST | `/api/unit-all-documents/` |

## Constants (reference limits in code)

From `properties/constants.py`:

- `MAX_UNIT_IMAGES = 10`
- `MAX_UNIT_DOCUMENTS = 5`

(Plan limits from DB may differ.)

## Related files

- `properties/models/unit_models.py`
- `properties/views/unit_views.py` (`UnitImageViewSet`, `UnitDocumentViewSet`)
- `properties/utils/__init__.py` (`generate_file_hash`)

## See also

- [Subscription limits](./02-subscription-and-usage-limits.md)
