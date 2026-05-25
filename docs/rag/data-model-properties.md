# RAG-006 — Data Model: `properties` App

**Metadata:** `id=RAG-006` | `tags=Building,Unit,Renter,RentRecord` | `app=properties` | `path=properties/models/`

## Building

- `owner` → User
- Address fields, `is_archived`
- Unique per owner: (`name`, `address_line`, `city`)

## Unit

- `owner`, optional `building`
- `unit` (identifier e.g. "101"), `unit_type`, `status` (`vacant`/`occupied`), `is_vacant`
- Geo: `latitude`, `longitude`
- `is_archived`, `rent_due_reminder`, etc.

## Renter

- `unit` FK, optional `user` (renter login)
- `phone` (unique per unit), `rent_amount`, `start_date`, `end_date`
- `status`: `active`, `notice_period`, `revoked`, `deactivated`
- KYC: `kyc_status`, onboarding: `onboarding_status`, `onboarding_token`
- Flags: `is_active`, `is_flagged`, `missed_rents`, agreement revocation fields
- Property alias: `renter.property` → returns `unit` (not Building)

## Caretaker

- `unit` FK, phone, date range

## RentRecord

- `renter`, `unit`, `owner`
- `rent_month` (DateField, 1st of month), `amount_paid`, `date_paid`
- `payment_status`: `PENDING`, `PAID`, `FAILED`
- `payment_mode`: cash, cheque, online, other
- Payout: `payout_status`, `payout_reference`, retry fields
- Razorpay: `razorpay_order_id`, `payment_link`
- `rent_due_date`, `late_fee`, `invoice_number`, `invoice_pdf`
- **Unique:** (`renter`, `rent_month`)
- Aliases: `.amount` → `amount_paid`, `.month`/`.year` from `rent_month`, `.due_date` → `rent_due_date`

## ExtraCharge

- `renter`, `unit`, `name`, `amount`, `due_date`, `status` (DUE/PAID/MISSED)

## UnitImage / UnitDocument

- `unit`, optional `renter`; file hash dedup in `clean()`

## RentAgreementDraft

- `user`, `renter`, `unit`, Leegality `leegality_document_id`

## PoliceVerification, ArchivedRenter, RentReminderLog

Supporting models for KYC, archive, reminder logs.
