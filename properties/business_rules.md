# Properties Module Business Rules

## 1. Purpose
The `properties` module manages rental property data for owners and renters. It controls creation, update, deletion, and access to:
- Buildings
- Units
- Caretakers
- Renters
- Rent payments
- Unit images and documents
- Draft agreements
- Payout retry operations

## 2. Ownership and Access Rules
- All property entities belong to a `User` owner.
- Owners can only create, update, delete, and view records for their own units and buildings.
- For any action on a child object, ownership is validated on the associated unit or building.
- If ownership mismatch occurs, the request is rejected with `PermissionDenied` or `ValidationError`.

## 3. Plan and Usage Limits
- The system enforces plan feature limits through `FeatureEnforcer`.
- Each create action checks the user's allowed limit for a feature key.
- Relevant feature keys include:
  - `max_buildings`
  - `max_units`
  - `max_caretakers`
  - `max_renters`
  - `rent_records`
  - `unit_images`
  - `unit_documents`
  - `rent_agreement_drafts`
- If a plan is expired and beyond grace period, the system falls back to free-plan limits for read access.
- Feature usage counts are incremented on create and decremented on destroy.

## 4. Caching Rules
- Querysets for list retrieval are cached for a single user.
- Cache keys include:
  - `buildings_user_{user.id}`
  - `units_user_{user.id}`
  - `caretakers_user_{user.id}`
  - `renters_user_{user.id}`
  - `rent_records_user_{user.id}`
  - `unit_images_user_{user.id}`
  - `unit_docs_user_{user.id}`
  - `rent_drafts_user_{user.id}`
- Cache is cleared after create, update, or delete operations for the affected object type.

## 5. Building Rules
- `Building` must belong to an owner.
- A single owner cannot create duplicate buildings with the same `name`, `address_line`, and `city`.
- `is_archived` controls whether a building is considered active or hidden.

## 6. Unit Rules
- `Unit` belongs to an owner and optionally a `Building`.
- `Unit` is unique for an owner by the combination of `unit`, `building`, and `address_line`.
- `Unit` fields include address, type, status, vacancy, reminders, verification, geo coordinates, and notes.
- `Unit.status` and `is_vacant` both describe occupancy and should remain consistent.
- Latitude must be between -90 and 90; longitude must be between -180 and 180.

## 7. Caretaker Rules
- `Caretaker` belongs to a `Unit`.
- Phone fields are validated by a shared phone regex.
- The caretaker record must belong to a unit owned by the requester.
- `end_date` cannot be earlier than `start_date`.
- Each unit can only have unique caretakers by phone number.

## 8. Renter Rules
- `Renter` belongs to a `Unit`.
- Renters can be in status: `active`, `notice_period`, `revoked`, or `deactivated`.
- Only renters with `active` or `notice_period` status are returned in default owner renter listings.
- `end_date` must not be earlier than `start_date`.
- Renters are unique within a unit by phone number.
- The system uses multiple tenant flags:
  - `is_active`
  - `is_agreement_revoked`
  - `revoked_by_owner`
  - `vacated_on`
- Renters can have a `rent_due_date` and optional WhatsApp contact.

## 9. RentRecord Rules
- `RentRecord` belongs to a `Renter`, `Unit`, and `Owner`.
- Each renter may have one rent record per `rent_month`.
- `amount_paid` cannot be negative.
- Payment date cannot be before the referenced rent month.
- The record is invalid if the selected `renter` does not belong to the selected `unit`.
- When created:
  - a Razorpay payment link is generated
  - a WhatsApp payment message is sent to the renter
- Payment and payout fields track status and retries:
  - `payment_mode`
  - `payout_status`
  - `payout_reference`
  - `payout_retry_count`
  - `razorpay_order_id`
  - `razorpay_payment_status`
- Invoice metadata is stored in `invoice_number` and `invoice_pdf`.

## 10. Unit Image and Document Rules
- `UnitImage` and `UnitDocument` belong to a `Unit` and optionally a `Renter`.
- Uploads are restricted by plan limits.
- The owner of the unit must match the requester.
- Document and image duplicates are blocked by hash-based comparison in model `clean()`.

## 11. Rent Agreement Draft Rules
- `RentAgreementDraft` belongs to a user, renter, and unit.
- The unit must be owned by the request user.
- The renter must belong to the selected unit.
- The draft creation is limited by `rent_agreement_drafts` usage.

## 12. Payout Retry and Owner Notification Rules
- `retry_payout_api` allows retrying failed payouts for rent records.
- The rent must belong to the current owner.
- Retry is allowed only when `payment_status == "PAID"` and `payout_status == "FAILED"`.
- After retry, if payout becomes `SUCCESS`, owner notification may be sent by WhatsApp.
- The owner phone number is expected to be stored in the owner profile in international format.

## 13. Owner Rent Reporting Rules
- `owner_rent_records` returns rent records belonging to the owner via renter->property ownership.
- `owner_rent_overview` returns a simple list of tenant, unit, amount, month, year, payment status, payout status, and invoice link.
- Owner-facing APIs are based on the assumption that rent records are linked to owner-owned properties.

## 14. Renter-Facing API Rules
- `get_latest_due_rent` returns the latest pending rent for the authenticated renter.
- Only renters with status `active` or `notice_period` can use renter-facing endpoints.
- `rent_history` returns all rent records ordered by most recent due date.
- `my_rent_records` returns rent records for the renter profile with invoice links for paid records.

## 15. Important Notes and Known Behaviors
- `Renter` and `Unit` relationships are strictly enforced: `renter.unit` must match the selected `unit` on rent creation.
- Default queries hide inactive or revoked renters by limiting status to `active` and `notice_period`.
- The system uses a combination of status flags and boolean fields, so consistency between `status`, `is_active`, and `is_agreement_revoked` is important.
- Some API-level code assumes the rent model exposes fields like `due_date`, `month`, and `year` in responses, so those values should be derived or mapped consistently in serializers.

## 16. Summary of Core Business Rules
1. Owners manage only their own buildings, units, caretakers, renters, and rent records.
2. Plan limits are enforced before creating new resources.
3. Cached object lists are cleared whenever data changes.
4. Rent records cannot be duplicated for the same renter and month.
5. Rent payment creation triggers external payment link generation and tenant notification.
6. Document and image uploads are limited and ownership-bound.
7. Draft agreement creation requires matching unit/renter ownership.
8. Only active or notice-period renters are shown in owner dashboards.
9. Payout retries are available only for previously paid rent records with failed payouts.

---

This business rules document is based on the current `properties` models, serializers, and view logic in the app.
 