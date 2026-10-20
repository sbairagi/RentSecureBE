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
| The create / edit / cancel form rules and their wording | `properties/services/rent_rules.py` |
| The workflows: part payment, cancel, reminder, receipt | `properties/services/rent_collection_service.py` |
| The data | `properties/models/rent_record_models.py` |
| Validation and the API shape | `properties/serializers/rent_record_serializers.py`, `properties/views/rent_record_views.py` |
| The receipt card and its PDF | `documents/receipt.py` |
| The tests that lock the rules | `properties/tests/test_rent_collection.py`, `properties/tests/test_rent_ledger_view.py` |

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
- The file names are `rent_receipt_<id>_<YYYYMM>.pdf` and
  `rent_receipt_<id>_<YYYYMM>_part<N>.pdf`.
- The receipt preview is the model the PDF is rendered from.

## Tests

```bash
DEBUG=True SECURE_SSL_REDIRECT=False SECURE_HSTS_SECONDS=0 \
  .venv/bin/python manage.py test properties.tests.test_rent_collection \
  properties.tests.test_rent_ledger_view
```

`DEBUG=True` is required when the shell exports `DEBUG=release` — the
environment wins over `.env`, and without it every API call answers `301` to
https.
