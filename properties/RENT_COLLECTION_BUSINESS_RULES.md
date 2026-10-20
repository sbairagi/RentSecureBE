# Rent Collection — Business Rules

> **These rules are binding.** Every human and every agent that touches the rent
> collection must preserve them. If a rule has to change, the change is made
> here first, then in the code, then in the tests — never only in the client.

| | |
|---|---|
| **Scope** | The rent collection ledger: rent records, part payments, cancellations, receipts, reminders and the reporting they feed. |
| **Owner of the rules** | The Django backend. The web client renders what the API sends. |
| **Read model** | `properties/services/rent_ledger_view.py` |
| **Form rules** | `properties/services/rent_rules.py` |
| **Write model** | `properties/services/rent_collection_service.py` |
| **Data** | `properties/models/rent_record_models.py` |
| **API shape & validation** | `properties/serializers/rent_record_serializers.py`, `properties/views/rent_record_views.py` |
| **Receipt card & PDF** | `documents/receipt.py`, `properties/services/receipt_service.py` |
| **Tests that lock the rules** | `properties/tests/test_rent_collection.py`, `properties/tests/test_rent_ledger_view.py` |
| **Client (renders only)** | `rentsecure-web/src/rentModel.js`, `src/RentCollectionPage.jsx`, `src/receipt.js`, `src/ReceiptModal.jsx` |

---

## 0. How to change a rule

1. Change the **backend** first — the read model, the form rules or the service.
2. Change **this file** in the same commit, with the new wording.
3. Change the **tests** in the same commit — a rule change that keeps the old
   tests green is not a rule change, it is a bug.
4. Only then touch the client, and only to render what the API now sends.
5. Never re-implement a rule in the client. If the client needs a number to
   decide something, the API has to ship it.

> A rule that exists only in the client is a bug: the API would accept a record
> the client refuses, or the ledger would show something the API would refuse.

---

## 1. The ledger row

### 1.1 One record per unit per month

A rent record is **one row per unit per month**. A second instalment is never a
second record — it is a **part payment** of the same record.

* The server refuses a second record for the same renter and period
  (`RentRecordViewSet.perform_create`).
* The client pre-checks the same rule against the rules catalogue
  (`duplicate.allowed = false`).

### 1.2 A rent record is never deleted

`DELETE /api/rent-records/{id}/` answers **405 Method Not Allowed**, always.
The row is removed from the books by being **cancelled**, never by being
deleted — the audit trail has to stay complete.

A unit that carries rent history cannot be deleted either
(`DELETE /api/units/{id}/` → 400).

### 1.3 Cancel instead of delete — the reason is mandatory

* `POST /api/rent-records/{id}/cancel/` with `{"reason": "..."}`.
* A blank reason is refused: **"A reason is required so the ledger history
  explains the cancellation."**
* A record can be cancelled only when it is still `pending` or `overdue` **and**
  no money has been received. A settled record, a cancelled record or a record
  with parts is refused.
* A cancelled record **stays visible** in the ledger and stops counting towards
  expected and collected rent.
* The cancellation is stamped with `cancelled_at` and `cancelled_by`.

### 1.4 A settled or cancelled record is locked

| Status | Edit | Cancel | Remind | Part payment | Receipt |
|---|---|---|---|---|---|
| `pending` | yes | yes (no money yet) | yes | yes | no (parts only) |
| `overdue` | yes | yes (no money yet) | yes | yes | no (parts only) |
| `paid` | **no** | **no** | **no** | **no** | yes |
| `cancelled` | **no** | **no** | no | **no** | no |

These are the flags the API ships in `ledger.row_state`
(`can_edit`, `can_cancel`, `can_remind`, `can_record_part`,
`can_send_receipt`, `is_locked`). The client never decides them.

### 1.5 What may be edited

| Field | Before any payment | After a payment |
|---|---|---|
| `notes` | yes | **yes** |
| `adjustment_reason` | yes | **yes** |
| `late_fee` | yes | **no — frozen** |
| `discount` | yes | **no — frozen** |
| `paid_on` | yes | no |
| everything else (`unit`, `renter`, `amount`, `due_date`, `payment_method`, `transaction_id`) | **no — locked at creation** | no |

* A locked record answers **400** with
  `"This rent record is {status} and can no longer be edited."`
* A frozen charge answers **400** with
  `"Cannot update fields: late_fee"`.
* Changing the unit or the renter of an existing record is refused.

### 1.6 Creating a record

* `unit` and `renter` are sent as **ids**; the server resolves them and refuses
  a unit of another owner, a renter of another unit, and a renter that is
  revoked or deactivated.
* `amount` must be **greater than zero** — *"Enter a rent amount greater than
  zero."* — and at most **10,00,000**.
* `late_fee` and `discount` must not be negative — *"Late fee and discount
  cannot be negative."*
* The creation limit of the owner's plan is enforced by the feature enforcer.

---

## 2. Money

### 2.1 The billed amount

```
total_due = amount + late_fee - discount
```

`RentRecord.total_due` is the only definition. The rules catalogue ships the
same components (`total_due.components`) so a form that is not saved yet can
preview the very same number.

### 2.2 The balance

```
balance = max(0, total_due - amount_paid)
```

`RentRecord.balance` is the only definition. The balance never goes negative:
an over-payment is impossible because a part may not exceed the balance.

### 2.3 `amount_paid` only grows through part payments

`amount_paid` is the sum of the parts of the record. It is **read-only** on the
API — a client can never set it directly.

### 2.4 Reporting

* **Collected** = Σ `amount_paid` (settled records; the income summary uses the
  successful payouts).
* **Pending / overdue** = Σ (`amount` + `late_fee` − `discount`) − Σ
  `amount_paid` — the money that is still to collect.
* A cancelled record counts towards neither.

### 2.5 How amounts and dates are rendered

* **Money** — `₹` with Indian digit grouping: `₹30,000`, `₹1,00,000`. The
  ledger rounds to the nearest rupee (half up); the charge breakdown keeps the
  paise (`+ ₹1,500.50 late fee`).
* **Ledger dates** — `05-Oct-2026`, with the Indian short month names
  (`Sept`, not `Sep`).
* **Receipt dates** — `05 Oct 2026` (the receipt keeps its own format, and the
  PDF and the preview use the very same one).
* The minus sign of a discount is the typographic one: `− ₹500 discount`.

---

## 3. Part payments

`POST /api/rent-records/{id}/payments/`

### 3.1 When a part may be recorded

All of these must hold:

1. the record is `pending` or `overdue` — a `paid` or `cancelled` record is
   refused;
2. `Unit.allow_partial_payments` is on — otherwise
   *"Part payments are off for this unit. Turn them on in Unit details to split
   the rent."*;
3. the balance is greater than zero — there is nothing left to split.

### 3.2 The amount

* **Greater than zero** — *"Enter the amount received in this part."*
* **At most the balance** — *"This part is larger than the remaining balance of
  ₹22,000."*
* The API ships the limit as `ledger.part_rules.max_amount` and the wording as
  `ledger.part_rules.messages`, so the client checks the same numbers.

### 3.3 The date

* `paid_on` is required.
* `paid_on` **may not be earlier than the rent due date** — *"The part date
  cannot be earlier than the rent due date (05 Oct 2026)."*
* The API ships the earliest allowed date as `ledger.part_rules.min_paid_on`
  and the date the form starts with as `ledger.part_rules.default_paid_on`:
  the due date, or **today** when the month is overdue and the due date has
  passed.

### 3.4 Settlement

* Every part increases `amount_paid` and is stored as a child row
  (`RentRecordPart`) that keeps its own amount, date, mode, reference and note.
* When `amount_paid` reaches `total_due`, the record becomes `paid` and
  `paid_on` and `payment_method` are stamped with the last part.
* A part that does not settle the month leaves the record `pending` (or
  `overdue`) — the row is then **partially paid**.

### 3.5 The receipt of a part

* **Every part carries its own receipt**, sent automatically to the renter.
  A failed delivery never undoes the payment.
* The file name is `rent_receipt_<rent id>_<YYYYMM>_part<N>.pdf`, where
  `<YYYYMM>` is the due date of the record and `<N>` is the 1-based position of
  the part in ledger order.
* The manual **Send receipt** action is only available for a settled month —
  the settlement receipt. A month that is still open is refused:
  *"This month is not settled yet. The receipt of every part payment is sent
  automatically…"*

### 3.6 The messages

The wording of the part rules lives in
`properties/services/rent_ledger_view.py::PART_PAYMENT_MESSAGES` and is shipped
to the client in `ledger.part_rules.messages`. The API answers with the very
same sentences.

---

## 4. Statuses, badges and actions

### 4.1 The four statuses

`pending`, `paid`, `overdue`, `cancelled`.

### 4.2 The badge set of a row

The API ships the badges in `ledger.status_badges` — an ordered list of
`{tone, label}`. The client renders them in that order and invents none.

| State | Badges (in order) |
|---|---|
| cancelled | `Cancelled` |
| settled | `Paid` |
| overdue, nothing received | `Overdue`, `Pending` |
| overdue, partly received | `Overdue`, `Partially paid`, `Pending` |
| pending, nothing received | `Pending` |
| pending, partly received | `Partially paid`, `Pending` |

**Pending means "the month is not fully settled"** — it is therefore on every
open row. **Partially paid means "money came in, the month is not settled"** —
it is never shown on a settled or cancelled row.

### 4.3 The actions of a row

The API ships them in `ledger.row_state`. The client may only offer an action
whose flag is `true`:

| Flag | Meaning |
|---|---|
| `can_edit` | the late fee, the discount, the adjustment reason and the notes may change |
| `can_cancel` | the record may be cancelled (a reason is still required) |
| `can_remind` | a reminder may be sent for the balance |
| `can_record_part` | another part may be recorded |
| `can_send_receipt` | the settlement receipt may be sent |
| `has_receipt` | the row shows a receipt (any money received) |
| `allows_parts` | the unit allows part payments at all |
| `is_locked` | the row is settled or cancelled |

### 4.4 The charge breakdown

`ledger.charge_breakdown` is an ordered list of `{tone, label}`:

* a late fee greater than zero → `+ ₹1,500 late fee` (tone `due`);
* a discount greater than zero → `− ₹500 discount` (tone `settled`).

An empty list means the month carries no extra charge.

### 4.5 The progress of a row

`ledger.progress` carries `paid_percent` (0–100, the share of the bill that
was received), `part_count`, `has_parts` and `settled`. The client draws the
bar with `paid_percent` — it never divides the amounts itself.

---

## 5. The receipt

### 5.1 The file names

| Receipt | File name |
|---|---|
| The month | `rent_receipt_<rent id>_<YYYYMM>.pdf` |
| One part | `rent_receipt_<rent id>_<YYYYMM>_part<N>.pdf` |

`<YYYYMM>` is the due date of the record, `<N>` the 1-based position of the
part in ledger order.

### 5.2 One card, three renderings

The receipt card is built **once**, in `documents/receipt.py::build_receipt`,
and rendered by

1. the PDF the owner downloads (`/api/documents/document/rent_receipt/<id>/pdf_receipt/`),
2. the PDF the renter receives by mail or WhatsApp,
3. the preview in the web client, which renders the very same model that the API
   ships in `ledger.receipt` and `parts[].receipt`.

**The preview and the PDF can never disagree** — they are the same model.

### 5.3 What a part receipt shows

* the amount of that part,
* the total received up to and including that part,
* the balance that is still open after that part,
* `Part <N> of <count>` and the file name of the part.

---

## 6. The API surface

| Endpoint | What it does |
|---|---|
| `GET /api/owner/rent-records/`, `GET /api/rent-records/` | The ledger: every record with its `ledger` view and its parts. |
| `GET /api/rent-records/rules/` | The rules catalogue: limits, flags and the wording of every form. |
| `POST /api/rent-records/` | Create a record. |
| `PATCH /api/rent-records/{id}/` | Update the allowed fields of an open record. |
| `POST /api/rent-records/{id}/payments/` | Record a part payment. |
| `POST /api/rent-records/{id}/cancel/` | Cancel a record with a reason. |
| `POST /api/rent-records/{id}/send-reminder/` | Remind the renter for the balance. |
| `POST /api/rent-records/{id}/send-receipt/` | Send the settlement receipt of a settled month. |
| `DELETE /api/rent-records/{id}/` | **405 — always.** |

The ledger view of one record:

```jsonc
{
  "ledger": {
    "row_state": { "status": "pending", "is_settled": false, "is_locked": false,
                   "is_partially_paid": true, "has_receipt": true, "allows_parts": true,
                   "can_edit": true, "can_cancel": false, "can_remind": true,
                   "can_send_receipt": false, "can_record_part": true },
    "amounts": { "amount": "30000.00", "amount_paid": "25000.00", "total_due": "30000.00",
                 "balance": "5000.00", "amount_display": "₹30,000", "has_balance": true,
                 "collected": true, "has_charges": false },
    "progress": { "paid_percent": 83, "part_count": 3, "has_parts": true, "settled": false },
    "status_badges": [ { "tone": "partial", "label": "Partially paid" },
                       { "tone": "pending", "label": "Pending" } ],
    "charge_breakdown": [ { "tone": "due", "label": "+ ₹1,500 late fee" } ],
    "part_rules": { "can_record_part": true, "max_amount": "5000.00",
                    "min_paid_on": "2026-10-05", "default_paid_on": "2026-10-05",
                    "due_date_display": "05-Oct-2026", "late_fee_included": false,
                    "messages": { "amount_required": "…", "amount_too_large": "…",
                                  "date_required": "…", "date_before_due": "…" } },
    "receipt": { "receipt_no": "rent_receipt_2_202610.pdf", "…": "…" },
    "receipt_filename": "rent_receipt_2_202610.pdf"
  }
}
```

and every part of a record carries `sequence`, `cumulative_amount`,
`receipt_filename` and its own `receipt` model.

---

## 7. What the client may and may not do

**May** — render the values the API sends, format a date or an amount for
display, and pre-check a form against the rules the API ships
(`ledger.part_rules`, `GET /api/rent-records/rules/`).

**May not** — recompute the balance or the total due, decide the badges,
decide which actions a row offers, invent the part limits or their wording,
or build the receipt card from the raw record.

The client is an adapter: `rentsecure-web/src/rentModel.js` reads the API
fields and does nothing else.

### The one exception

A form that is **not saved yet** cannot be previewed by the server without a
round trip, so the create/edit form previews its total with the components the
rules catalogue ships (`total_due.components`). The **authoritative** total is
always the one the server computes and returns.

---

## 8. The checklist — do not break these

- [ ] A rent record is never deleted; it is cancelled with a reason.
- [ ] A settled or a cancelled record is fully locked.
- [ ] A paid record cannot be cancelled; a record with money cannot be cancelled either.
- [ ] The late fee and the discount freeze as soon as money has been received.
- [ ] A part needs the unit flag, an open month, a positive amount, an amount
      within the balance and a date on or after the due date.
- [ ] The last part settles the month.
- [ ] Every part carries its own receipt; the settlement receipt belongs to a
      settled month.
- [ ] `total_due = amount + late_fee - discount` and
      `balance = max(0, total_due - amount_paid)`.
- [ ] Pending means "not fully settled" and is on every open row.
- [ ] The badge set, the actions, the breakdown, the progress and the receipt
      come from the API — the client invents none of them.
- [ ] The receipt preview is the model the PDF is rendered from.
- [ ] The file names are `rent_receipt_<id>_<YYYYMM>.pdf` and
      `rent_receipt_<id>_<YYYYMM>_part<N>.pdf`.
- [ ] Every rule change lands in this file and in the tests.

---

## 9. Related documentation

* [`docs/business-rules/08-rent-records.md`](../docs/business-rules/08-rent-records.md) —
  the API surface of the rent records.
* [`docs/business-rules/20-documents-and-pdfs.md`](../docs/business-rules/20-documents-and-pdfs.md) —
  the receipt documents.
* [`docs/business-rules/12-owner-reporting.md`](../docs/business-rules/12-owner-reporting.md) —
  how the ledger feeds the reports.
* [`properties/business_rules.md`](../business_rules.md) — the index of the
  business rules of the properties module.
