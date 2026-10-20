# Rent Collection — Business Rules

> **These rules are binding.** Every human and every agent that touches the rent
> collection must preserve them. If a rule has to change, the change is made
> here first, then in the code, then in the tests — never only in the client.

| | |
|---|---|
| **Scope** | The rent collection ledger: the billing cycle, rent records, part payments, cancellations, receipts, reminders, the filters and the pagination of the ledger, and the reporting they feed. |
| **Owner of the rules** | The Django backend. The web client renders what the API sends. |
| **Read model** | `properties/services/rent_ledger_view.py` |
| **Billing cycle** | `properties/services/rent_cycle.py` |
| **The ledger query: filters, facets, pagination** | `properties/services/rent_ledger_query.py` |
| **Form rules** | `properties/services/rent_rules.py` |
| **Write model** | `properties/services/rent_collection_service.py` |
| **Data** | `properties/models/rent_record_models.py` |
| **API shape & validation** | `properties/serializers/rent_record_serializers.py`, `properties/views/rent_record_views.py` |
| **Receipt card & PDF** | `documents/receipt.py`, `properties/services/receipt_service.py` |
| **Tests that lock the rules** | `properties/tests/test_rent_collection.py`, `properties/tests/test_rent_ledger_view.py`, `properties/tests/test_rent_cycle.py`, `properties/tests/test_rent_ledger_query.py` |
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
* Which month may be created at all is the **billing cycle** of the unit — see
  §2.

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
* A `discount` may not be larger than the bill it discounts — *"The discount
  cannot be more than the rent that was billed (₹30,000)."*
* A unit is billed **once for a month**: a second record for the same
  `(unit, due_date)` pair is refused — *"A rent record already exists for this
  unit and month."* The pair is the one the database guards
  (`unique_together`), so a new renter for the same unit and month is refused
  as well.
* A new record starts **unpaid**: a `paid_on` that arrives with the record is
  ignored (dropped before any other rule looks at it). The date may be edited
  later, while the month is open (§1.5).
* The creation limit of the owner's plan is enforced by the feature enforcer.
* A record may only be created for the month the **billing cycle** of its unit
  allows — see §2.

---

## 2. The billing cycle of a unit

A unit is billed **one month at a time**. The ledger of a unit is a **chain of
months**, and the chain never breaks, never skips a month and never bills a
month twice.

The rules live in `properties/services/rent_cycle.py` and are enforced in
`RentRecordViewSet.perform_create`.

### 2.1 The anchor

The anchor of the cycle is the **most recent rent record of the unit** — the
one with the greatest `due_date`; the greater `id` breaks a tie. The anchor
decides **which** month may be billed next.

The **open months** of the unit decide **whether** a month may be billed at
all: a month is open while it is `pending` or `overdue` — paid in part or not
at all. The **oldest** open month holds the chain, whatever happened to the
months that came after it. That is what keeps an imported history from opening
a hole in the chain.

### 2.2 Which month may be billed

| The anchor | The next cycle |
|---|---|
| *none — the unit has no rent history yet* | **any date may be billed** — the first record starts the chain |
| `paid` (settled) | the month that follows it, on the same day of the month |
| `pending` / `overdue` (open — fully or partly paid) | **nothing — the chain is blocked** |
| `cancelled` | the month that follows it, on the same day of the month |

* A settled month opens **exactly one** month: the one that follows it. The
  month after that may not be billed while the new one is open.
* An open month **blocks** the chain until it is settled: *"The rent for
  October 2026 is still open — ₹30,000 is still due. Settle it before you bill
  November 2026."*
* **Every** open month blocks the chain, not only the newest one. A history
  that was imported around the rules — August settled, September never settled,
  October billed anyway — still holds the chain on September, and the next
  month is refused until September is settled.
* A cancelled month is voided: the chain **continues** with the month that
  follows it. A cancelled month never blocks the chain and never leaves a gap
  in it.
* A unit without a rent history may start at **any** due date — the chain
  begins where the owner begins it.

### 2.3 The day of the month is clamped to the length of the month

The next month keeps the **day of the month** of the anchor, clamped to the
length of the month that follows:

| The anchor | The month that follows | The next cycle |
|---|---|---|
| 31 January | February — 28 days | **28 February** |
| 31 January | February — 29 days (leap year) | **29 February** |
| 31 October | November — 30 days | **30 November** |
| 30 April | May — 31 days | **30 May** |
| 05 October | November — 30 days | **05 November** |
| 05 December | January — 31 days | **05 January** |

The clamp is **one way only**: once the chain has been clamped to the 28th of
February, the next cycle keeps the 28th — the chain never jumps back to the
31st.

The rule lives in `properties/services/rent_cycle.py::next_cycle_due_date`.

### 2.4 What the server refuses

`POST /api/rent-records/` refuses a record that breaks the chain — always with
**400** and the reason:

| The request | The answer |
|---|---|
| a month that skips one | *"The next cycle for this unit is due 05-Nov-2026 (November has 30 days)."* |
| a month while an earlier month is open | *"The rent for September 2026 is still open — ₹30,000 is still due. Settle it before you bill November 2026."* |
| the month that is already billed for the unit | *"A rent record already exists for this unit and month."* |

A unit of another owner is refused by the ownership guard, not by the cycle.

### 2.5 The cycle state the API ships

`GET /api/rent-records/cycle/?unit=<id>` — the cycle of one unit. The unit must
belong to the owner; a unit of another owner answers **404**.

```jsonc
{
  "unit": 7,
  "has_cycle": true,
  "allowed": true,
  "previous_due_date": "2026-10-05",
  "previous_due_date_display": "05-Oct-2026",
  "previous_month": "October 2026",
  "previous_status": "paid",
  "previous_is_settled": true,
  "previous_is_open": false,
  "blocking_due_date": null,
  "blocking_month": null,
  "balance_due": "0.00",
  "balance_due_display": "₹0",
  "next_due_date": "2026-11-05",
  "next_due_date_display": "05-Nov-2026",
  "next_month": "November 2026",
  "next_month_days": 30,
  "clamped": false,
  "clamp_note": "",
  "message": "The rent for October 2026 is settled — the next cycle is due 05-Nov-2026. November has 30 days.",
  "blocked_message": "",
  "mismatch_message": "The next cycle for this unit is due 05-Nov-2026 (November has 30 days)."
}
```

* `allowed` — whether a month may be billed at all right now.
* `next_due_date` — the only due date the next record may carry.
* `next_month_days` — the length of that month (28, 29, 30 or 31).
* `clamped` / `clamp_note` — whether the day had to be clamped, and why.
* `blocking_due_date` / `blocking_month` — the open month that holds the
  chain, when there is one.
* `message` — the wording of the cycle, ready to be shown.
* `blocked_message` — why the chain is blocked (empty when it is not).
* `mismatch_message` — what to say when the date is not the cycle's date.

A unit without a rent history answers `has_cycle: false`, `allowed: true` and
no next date — the first record starts the chain.

### 2.6 The rules catalogue

`GET /api/rent-records/rules/` carries `rules.cycle`: `one_month_at_a_time`
and the wording of the rule. The catalogue states the **rule**, the cycle
endpoint states the **month** of one unit.

### 2.7 What the client may do with it

The client may show `message`, pre-fill the due date with `next_due_date` and
refuse a date that is not `next_due_date` (`mismatch_message`) or a month while
the chain is blocked (`blocked_message`).

The client may **not** compute a month of its own, and it may not let a month
through that the server would refuse.

The message is shown **under the field row**, never inside a field — the cycle
must not break the alignment of the form, and it must not turn an
informational month into a field error. A refusal belongs in the error box the
form already has.

---

## 3. Money

### 3.1 The billed amount

```
total_due = max(0, amount + late_fee - discount)
```

`RentRecord.total_due` is the only definition. The rules catalogue ships the
same components (`total_due.components`) so a form that is not saved yet can
preview the very same number.

The bill never turns **negative**: a discount may not be larger than the bill
it discounts (§1.6), and the total is clamped to zero for the records that
were written before that rule existed. A month that owes the renter money is
not a thing the ledger can show.

### 3.2 The balance

```
balance = max(0, total_due - amount_paid)
```

`RentRecord.balance` is the only definition. The balance never goes negative:
an over-payment is impossible because a part may not exceed the balance.

### 3.3 `amount_paid` only grows through part payments

`amount_paid` is the sum of the parts of the record. It is **read-only** on the
API — a client can never set it directly.

### 3.4 Reporting

* **Collected** = Σ `amount_paid` (settled records; the income summary uses the
  successful payouts).
* **Pending / overdue** = Σ (`amount` + `late_fee` − `discount`) − Σ
  `amount_paid` — the money that is still to collect.
* A cancelled record counts towards neither.

### 3.5 How amounts and dates are rendered

* **Money** — `₹` with Indian digit grouping: `₹30,000`, `₹1,00,000`. The
  ledger rounds to the nearest rupee (half up); the charge breakdown keeps the
  paise (`+ ₹1,500.50 late fee`).
* **Ledger dates** — `05-Oct-2026`, with the Indian short month names
  (`Sept`, not `Sep`).
* **Receipt dates** — `05 Oct 2026` (the receipt keeps its own format, and the
  PDF and the preview use the very same one).
* The minus sign of a discount is the typographic one: `− ₹500 discount`.

---

## 4. Part payments

`POST /api/rent-records/{id}/payments/`

### 4.1 When a part may be recorded

All of these must hold:

1. the record is `pending` or `overdue` — a `paid` or `cancelled` record is
   refused;
2. `Unit.allow_partial_payments` is on — otherwise
   *"Part payments are off for this unit. Turn them on in Unit details to split
   the rent."*;
3. the balance is greater than zero — there is nothing left to split.

### 4.2 The amount

* **Greater than zero** — *"Enter the amount received in this part."*
* **At most the balance** — *"This part is larger than the remaining balance of
  ₹22,000."*
* The API ships the limit as `ledger.part_rules.max_amount` and the wording as
  `ledger.part_rules.messages`, so the client checks the same numbers.

### 4.3 The date

* `paid_on` is required.
* `paid_on` **may not be earlier than the rent due date** — *"The part date
  cannot be earlier than the rent due date (05 Oct 2026)."*
* The API ships the earliest allowed date as `ledger.part_rules.min_paid_on`
  and the date the form starts with as `ledger.part_rules.default_paid_on`:
  the due date, or **today** when the month is overdue and the due date has
  passed.

### 4.4 Settlement

* Every part increases `amount_paid` and is stored as a child row
  (`RentRecordPart`) that keeps its own amount, date, mode, reference and note.
* When `amount_paid` reaches `total_due`, the record becomes `paid` and
  `paid_on` and `payment_method` are stamped with the last part.
* A part that does not settle the month leaves the record `pending` (or
  `overdue`) — the row is then **partially paid**.
* The part and the new total of the record are written in **one transaction**,
  with the record **locked** for the write. Two parts of the same month can
  therefore never be counted twice, and a part is always measured against the
  balance of that very moment. The receipt of the part is sent **after** the
  transaction has been committed — a slow mail server never holds the lock.

### 4.5 The receipt of a part

* **Every part carries its own receipt**, sent automatically to the renter.
  A failed delivery never undoes the payment.
* The file name is `rent_receipt_<rent id>_<YYYYMM>_part<N>.pdf`, where
  `<YYYYMM>` is the due date of the record and `<N>` is the 1-based position of
  the part in ledger order.
* The manual **Send receipt** action is only available for a settled month —
  the settlement receipt. A month that is still open is refused:
  *"This month is not settled yet. The receipt of every part payment is sent
  automatically…"*

### 4.6 The messages

The wording of the part rules lives in
`properties/services/rent_ledger_view.py::PART_PAYMENT_MESSAGES` and is shipped
to the client in `ledger.part_rules.messages`. The API answers with the very
same sentences.

---

## 5. Statuses, badges and actions

### 5.1 The four statuses

`pending`, `paid`, `overdue`, `cancelled`.

### 5.2 The badge set of a row

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

### 5.3 The actions of a row

The API ships them in `ledger.row_state`. The client may only offer an action
whose flag is `true`:

| Flag | Meaning |
|---|---|
| `can_edit` | the late fee, the discount, the adjustment reason and the notes may change |
| `can_cancel` | the record may be cancelled (a reason is still required) |
| `can_remind` | a reminder may be sent for the balance — **false** for a settled or a cancelled row and for a row whose balance is already zero |
| `can_record_part` | another part may be recorded |
| `can_send_receipt` | the settlement receipt may be sent |
| `has_receipt` | the row shows a receipt (any money received) |
| `allows_parts` | the unit allows part payments at all |
| `is_locked` | the row is settled or cancelled |

The client renders the **Remind** action as a locked chip when `can_remind` is
`false` — it never offers an action the server would refuse.

### 5.4 The charge breakdown

`ledger.charge_breakdown` is an ordered list of `{tone, label}`:

* a late fee greater than zero → `+ ₹1,500 late fee` (tone `due`);
* a discount greater than zero → `− ₹500 discount` (tone `settled`).

An empty list means the month carries no extra charge.

### 5.5 The progress of a row

`ledger.progress` carries `paid_percent` (0–100, the share of the bill that
was received), `part_count`, `has_parts` and `settled`. The client draws the
bar with `paid_percent` — it never divides the amounts itself.

---

## 6. The receipt

### 6.1 The file names

| Receipt | File name |
|---|---|
| The month | `rent_receipt_<rent id>_<YYYYMM>.pdf` |
| One part | `rent_receipt_<rent id>_<YYYYMM>_part<N>.pdf` |

`<YYYYMM>` is the due date of the record, `<N>` the 1-based position of the
part in ledger order.

### 6.2 One card, three renderings

The receipt card is built **once**, in `documents/receipt.py::build_receipt`,
and rendered by

1. the PDF the owner downloads (`/api/documents/document/rent_receipt/<id>/pdf_receipt/`),
2. the PDF the renter receives by mail or WhatsApp,
3. the preview in the web client, which renders the very same model that the API
   ships in `ledger.receipt` and `parts[].receipt`.

**The preview and the PDF can never disagree** — they are the same model.

### 6.3 What a part receipt shows

* the amount of that part,
* the total received up to and including that part,
* the balance that is still open after that part,
* `Part <N> of <count>` and the file name of the part.

### 6.4 Sending the reminder and the receipt

| Situation | The answer |
|---|---|
| a cancelled month | **400** — *"This rent record was cancelled — there is nothing to follow up on."* The voided month never talks to the renter again. |
| a settled month | **400** — *"This rent record is settled — there is nothing to follow up on."* |
| a renter without a phone number | **400** — *"This renter has no phone number on file to remind."* |
| a month that is not settled, asked for a receipt | **400** — the receipt of every part is sent automatically. |

Both endpoints answer with the truth about the delivery:

```jsonc
{ "sent": true,  "receipt_sent_at": "2026-10-06T09:12:44Z" }
{ "sent": false, "receipt_sent_at": null }
```

* `sent` is `true` only when the message **really** left — the mail server
  accepted it, or WhatsApp accepted it. A failed delivery answers `false`, and
  the client says so instead of reporting a success.
* `receipt_sent_at` is stamped **only** on a real delivery: a receipt that
  never left the building was never sent.
* The month names of the reminder and of the receipt come from one fixed
  list (`documents/receipt.py::MONTH_NAMES`), so they never change with the
  locale of the machine the server runs on.

---

## 7. The ledger query — the filters, the facets and the pagination

A ledger that grows is not a list any more: the owner needs to narrow it down
and to walk through it. Both are **server** work — the client sends the
filters it applied and the page it wants, and the server answers with the rows
of that page, the grouped filter options and the state of the pagination.

The rules live in `properties/services/rent_ledger_query.py`.

### 7.1 The filters

| Filter | The parameter | The values |
|---|---|---|
| Building | `building` | the ids of the buildings |
| Unit | `unit` | the ids of the units |
| Status | `status` | `pending`, `overdue`, `paid`, `cancelled` |

* Every filter is a **multi-select**: `?status=paid&status=overdue` and
  `?status=paid,overdue` are the same request.
* The filters are **and**ed, the values inside a filter are **or**ed:
  `?building=1&status=paid` are the records of the building *and* paid.
* A value of another owner matches nothing — a filter never leaves the ledger
  of the owner.
* A status that does not exist is ignored.
* The search (`search`) narrows the ledger down to the renter, the unit, the
  building, the transaction reference or the notes.

### 7.2 The facets — the options of the filters

The options of every filter are **grouped by the server**, and every option
carries the number of records behind it:

```jsonc
"filters": {
  "building": { "key": "building", "label": "Building", "searchable": true,
                "options": [ { "value": "1", "label": "Maple Heights", "meta": "",
                               "count": 12, "selected": false } ] },
  "unit":      { "key": "unit", "label": "Unit", "searchable": true,
                 "options": [ { "value": "7", "label": "B-101", "meta": "Maple Heights",
                                "count": 3, "selected": true } ] },
  "status":    { "key": "status", "label": "Status", "searchable": true,
                 "options": [ { "value": "paid", "label": "Paid", "meta": "",
                                "count": 6, "selected": false } ] }
}
```

* The options of a filter are counted with the **other** filters applied — the
  units that are offered are the units of the building that was picked.
* The label of a status is the label of its badge (`Paid`, `Pending`,
  `Overdue`, `Cancelled`).
* The label of a unit carries the building it belongs to in `meta`.
* The values that are picked carry `selected: true`.

### 7.3 The pagination

| Parameter | What it does |
|---|---|
| `page` | the page that is asked for — a page beyond the last one lands on the last one |
| `page_size` | the rows a page may hold — **10, 25, 50, 75 or 100**; any other size is refused and the default (25) is used |

The answer carries the state of the pagination:

```jsonc
{ "count": 57, "page": 2, "page_size": 25, "total_pages": 3,
  "previous_page": 1, "next_page": 3, "first_row": 26, "last_row": 50,
  "page_sizes": [10, 25, 50, 75, 100] }
```

* The rows are ordered by the month (`-due_date`) and by the id — the order
  never moves, so a page never repeats a row and never skips one.
* The **counts** (`summary`) belong to the whole filtered ledger, not to the
  page on screen: `paid`, `pending`, `overdue`, `cancelled` and
  `partially_paid`.
* The client may only ask for a page and a page size the server offers.

### 7.4 The history of a record

The story of one month is three things in one list:

* the **audit trail** — every change the record went through, kept by
  `django-simple-history`: `+` (created), `~` (updated), `-` (deleted);
* the **action log** — every action a user took on the record: the month
  was created, the details were edited, the month was cancelled and why,
  the reminder was sent, the receipt was delivered (or could not be);
* the **part payments** — every instalment that was received against the
  month, with its amount, its date, its mode, its reference and its note.

All three are merged, ordered **newest first**, and the list never grows
past **50 entries**.

```jsonc
[ { "id": 12, "action": "part", "changed_by": "owner@rentsecure.test",
    "timestamp": "2026-10-20T13:00:36.252737+00:00",
    "data": { "amount": "10000.00", "paid_on": "2026-10-08",
              "payment_method": "upi", "transaction_id": "", "note": "Second instalment" } },
  { "id": 3, "action": "receipt_sent", "changed_by": "owner@rentsecure.test",
    "timestamp": "2026-10-20T13:00:36.139383+00:00",
    "data": { "action": "receipt_sent", "summary": "Receipt not delivered",
              "detail": "The receipt could not be delivered to the renter.",
              "outcome": "failed" } } ]
```

* The `data` of a change is the **snapshot the record left behind** — the
  money of the month as it stood at that moment.
* The `data` of a part is the part itself.
* The `data` of an action says **what was done** (`summary`), **the words
  behind it** (`detail`) and **how it ended** (`outcome`: `sent`, `failed`
  or `recorded`).
* `changed_by` is empty when the change was made by the API itself.
* A record of another owner answers **403**; a record that does not exist
  answers **404**.
* The client renders the entries it gets — it never builds an entry of its
  own.

#### The actions of a user

Every action the owner takes leaves a row in the action log
(`properties/models/rent_record_models.py::RentRecordAction`):

| Kind | Written by | When |
|---|---|---|
| `created` | `perform_create` | the month was created |
| `edited` | `perform_update` | the details of the month were changed |
| `cancelled` | `cancel_rent_record` | the month was voided — the reason is the detail |
| `receipt_sent` | `send_rent_receipt` | a receipt was sent — **also when it could not be delivered** |
| `reminder_sent` | `send_rent_reminder` | a reminder was sent — **also when it could not be delivered** |

* A part payment needs no action row — the part itself is the entry.
* An action that changed the record carries the id of the audit entry it
  explains (`history_id`), so one action is never listed twice.
* A save that only stamps a bookkeeping field (`receipt_sent_at`,
  `last_reminded_at`, `payment_link`) is **not** written to the audit trail
  (`skip_history_when_saving`) — the action log is what tells the owner
  about it.
* A trail that cannot be written never breaks the action it describes.

---

## 8. The API surface

| Endpoint | What it does |
|---|---|
| `GET /api/owner/rent-records/`, `GET /api/rent-records/` | The ledger: every record with its `ledger` view and its parts. |
| `GET /api/rent-records/ledger/` | The ledger of the owner — one page of rows, the grouped filter options, the counts and the pagination state (§7). |
| `GET /api/rent-records/rules/` | The rules catalogue: limits, flags and the wording of every form. |
| `GET /api/rent-records/cycle/?unit=<id>` | The billing cycle of one unit: which month may be billed next and why (§2). |
| `POST /api/rent-records/` | Create a record — only for the month the cycle allows (§2). |
| `PATCH /api/rent-records/{id}/` | Update the allowed fields of an open record. |
| `POST /api/rent-records/{id}/payments/` | Record a part payment. |
| `POST /api/rent-records/{id}/cancel/` | Cancel a record with a reason. |
| `POST /api/rent-records/{id}/send-reminder/` | Remind the renter for the balance — answers `sent` (§6.4). |
| `POST /api/rent-records/{id}/send-receipt/` | Send the settlement receipt of a settled month — answers `sent` (§6.4). |
| `GET /api/rent-records/{id}/history/` | The history of one record — the audit trail and the part payments (§7.4). |
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

## 9. What the client may and may not do

**May** — render the values the API sends, format a date or an amount for
display, and pre-check a form against the rules the API ships
(`ledger.part_rules`, `GET /api/rent-records/rules/`).

**May not** — recompute the balance or the total due, decide the badges,
decide which actions a row offers, invent the part limits or their wording,
compute the month of the billing cycle, group or count the ledger on its own,
build the receipt card from the raw record, or build an entry of the history
of a record.

The client is an adapter: `rentsecure-web/src/rentModel.js` reads the API
fields and does nothing else.

### The one exception

A form that is **not saved yet** cannot be previewed by the server without a
round trip, so the create/edit form previews its total with the components the
rules catalogue ships (`total_due.components`). The **authoritative** total is
always the one the server computes and returns.

### The cycle is not an exception

The billing cycle is **not** pre-computed by the client. The client asks
`GET /api/rent-records/cycle/?unit=<id>` which month may be billed, shows the
wording the server sends and refuses a date the server would refuse (§2.7).

### The ledger query is not an exception either

The filters, their options, their counts and the pagination are the server's
(§7). The client sends the filters it applied and the page it wants, and it
renders the rows, the options and the pagination state it gets back. It may
search **inside** the options the server sent — it may not build an option of
its own, count the ledger itself or slice a page out of a list it holds.

---

## 10. The checklist — do not break these

- [ ] A rent record is never deleted; it is cancelled with a reason.
- [ ] A settled or a cancelled record is fully locked.
- [ ] A paid record cannot be cancelled; a record with money cannot be cancelled either.
- [ ] A unit is billed once for a month: the second record of the same
      `(unit, due_date)` pair is refused.
- [ ] A new record starts unpaid — a `paid_on` that arrives with it is ignored.
- [ ] The late fee and the discount freeze as soon as money has been received.
- [ ] A discount may never be larger than the bill it discounts, and the total
      of a month is never negative.
- [ ] A part needs the unit flag, an open month, a positive amount, an amount
      within the balance and a date on or after the due date.
- [ ] A part and the new total of its record are written in one transaction,
      with the record locked for the write.
- [ ] The last part settles the month.
- [ ] Every part carries its own receipt; the settlement receipt belongs to a
      settled month.
- [ ] `total_due = max(0, amount + late_fee - discount)` and
      `balance = max(0, total_due - amount_paid)`.
- [ ] Pending means "not fully settled" and is on every open row.
- [ ] The badge set, the actions, the breakdown, the progress and the receipt
      come from the API — the client invents none of them.
- [ ] The receipt preview is the model the PDF is rendered from.
- [ ] The file names are `rent_receipt_<id>_<YYYYMM>.pdf` and
      `rent_receipt_<id>_<YYYYMM>_part<N>.pdf`.
- [ ] A unit is billed one month at a time: only the month the cycle allows is
      created, and a skipped month is refused.
- [ ] An open month blocks the next month — **every** open month, not only the
      newest one; a settled month opens exactly the month that follows it; a
      cancelled month lets the chain continue.
- [ ] The day of the month is clamped to the length of the month that follows
      (31 January → 28/29 February) and the clamp is never undone.
- [ ] A cancelled month is never reminded and never gets a receipt.
- [ ] A delivery that failed answers `false` — the client never reports a
      success that did not happen.
- [ ] The month names come from one fixed list — never from the locale of the
      machine the server runs on.
- [ ] The ledger is queried on the server: the filters, the grouped options and
      the pagination.
- [ ] The page size is one of 10, 25, 50, 75, 100 — anything else falls back
      to 25.
- [ ] Every filter option carries the number of records behind it, and the
      values that are picked are marked.
- [ ] The counts above the ledger belong to the whole filtered ledger, not to
      the page on screen.
- [ ] The history of a record is the server's: the audit trail, the actions of
      the user and the part payments, merged, newest first, at most 50 entries.
- [ ] Every action of a user leaves a trail — including a receipt or a
      reminder that could **not** be delivered.
- [ ] One action is never listed twice: the action explains the audit entry it
      caused.
- [ ] Every rule change lands in this file and in the tests.

---

## 11. Related documentation

* [`docs/business-rules/08-rent-records.md`](../docs/business-rules/08-rent-records.md) —
  the API surface of the rent records.
* [`docs/business-rules/20-documents-and-pdfs.md`](../docs/business-rules/20-documents-and-pdfs.md) —
  the receipt documents.
* [`docs/business-rules/12-owner-reporting.md`](../docs/business-rules/12-owner-reporting.md) —
  how the ledger feeds the reports.
* [`properties/business_rules.md`](../business_rules.md) — the index of the
  business rules of the properties module.
