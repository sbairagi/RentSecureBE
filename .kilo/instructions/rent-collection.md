# Rent Collection Rules

The rent collection is **owned by the backend**. The clients render what the
API sends; they never decide a rule of their own.

**Read `properties/RENT_COLLECTION_BUSINESS_RULES.md` before touching anything
in this area.** It is the binding contract — the ledger row, the lock matrix,
the part-payment rules, the money rules, the receipts, the API shape, the
reporting rules and the client contract. It lives next to the modules that
implement it.

## Where the rules live

| Concern | File |
|---|---|
| The ledger row: state, badges, amounts, progress, charges, part rules, receipt | `properties/services/rent_ledger_view.py` |
| The billing cycle of a unit: which month may be billed next, and why | `properties/services/rent_cycle.py` |
| The ledger query: the filters, their grouped options and the pagination | `properties/services/rent_ledger_query.py` |
| The create / edit / cancel form rules and their wording | `properties/services/rent_rules.py` |
| The workflows: part payment, cancel, reminder, receipt | `properties/services/rent_collection_service.py` |
| The action log: every action a user takes on a record | `properties/services/rent_actions.py` |
| The history of a record: the audit trail, the actions and the parts, merged | `properties/services/rent_history.py` |
| The data | `properties/models/rent_record_models.py` |
| Validation and the API shape | `properties/serializers/rent_record_serializers.py`, `properties/views/rent_record_views.py` |
| The receipt card and its PDF | `documents/receipt.py` |
| The tests that lock the rules | `properties/tests/test_rent_collection.py`, `properties/tests/test_rent_ledger_view.py`, `properties/tests/test_rent_cycle.py`, `properties/tests/test_rent_ledger_query.py`, `properties/tests/test_rent_history.py` |

## Rules for every change

1. **Change the backend first.** If a rule moves, it moves in the service, the
   read model or the model — never only in a client.
2. **Update `properties/RENT_COLLECTION_BUSINESS_RULES.md` in the same change.**
   The document is the contract, the code is the implementation.
3. **Update the tests in the same change.** A rule change that keeps the old
   tests green is a bug, not a change.
4. **Ship what the client needs.** A row state, a badge, a limit or a message
   that the client has to decide belongs in the API.
5. **Never re-implement a rule in `rentsecure-web`.** `src/rentModel.js` is an
   adapter over the API fields and nothing else.

## The rules that must not be broken

- A rent record is **never deleted** — it is cancelled with a mandatory reason
  and stays visible.
- A **settled** or **cancelled** record is fully locked; after money arrived
  the late fee and the discount freeze as well.
- A **part payment** needs the unit flag, an open month, an amount `> 0`, an
  amount within the balance and a date on or after the due date. The last part
  settles the month.
- `total_due = amount + late_fee - discount`,
  `balance = max(0, total_due - amount_paid)`.
- **Pending** means "not fully settled" and sits on every open row.
- Every part carries its own receipt; the settlement receipt belongs to a
  settled month.
- A unit is billed **one month at a time**: only the month the billing cycle
  allows is created. A settled month opens exactly the month that follows it, an
  open month blocks the chain, a cancelled month lets it continue, and the day
  of the month is clamped to the length of the month that follows. **Every**
  open month of a unit blocks the chain, not only the newest one.
- A unit is billed **once for a month**: the second record of the same
  `(unit, due_date)` pair is refused.
- The bill is never negative: a discount may not be larger than the bill it
  discounts.
- A part payment and the new total of its record are written in one
  transaction, with the record locked for the write.
- A delivery that failed answers `false` — the client never reports a success
  that did not happen. A cancelled month is never reminded and never gets a
  receipt.
- The ledger is **queried on the server**: the filters (building, unit,
  status), their grouped options and the pagination (10, 25, 50, 75 or 100
  rows a page) come from the ledger endpoint. The client renders them.
- The file names are `rent_receipt_<id>_<YYYYMM>.pdf` and
  `rent_receipt_<id>_<YYYYMM>_part<N>.pdf`.
- The receipt preview is the model the PDF is rendered from.
- The **history of a record** is the server's: the audit trail, the actions of the
  user and the part payments, merged, newest first, at most **50** entries. The
  client renders the entries it gets.
- **Every** action of a user leaves a trail — a create, an edit, a cancel, a
  receipt and a reminder, **also when the delivery failed**. One action is
  never listed twice: the action explains the audit entry it caused.
- A trail that cannot be written never breaks the action it describes.

## Tests

```bash
DEBUG=True SECURE_SSL_REDIRECT=False SECURE_HSTS_SECONDS=0 \
  .venv/bin/python manage.py test properties.tests.test_rent_collection \
  properties.tests.test_rent_ledger_view properties.tests.test_rent_cycle \
  properties.tests.test_rent_ledger_query \
  properties.tests.test_rent_collection_edge_cases \
  properties.tests.test_rent_history
```

`DEBUG=True` is required when the shell exports `DEBUG=release` — the
environment wins over `.env`, and without it every API call answers `301` to
https.
