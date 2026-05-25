# Bugs — `finance` app

CA profiles, tax submissions, document export.

---

## FIN-001 | P1 — `TaxSubmissionToCAViewSet.get_queryset` invalid filter

**File:** `finance/views.py:24`

```python
return TaxSubmissionToCA.objects.filter(tax_summary__user=self.request.user)
```

**Model:** `TaxSubmissionToCA` has `user` FK, **no** `tax_summary` relation.

**Impact:** `FieldError` when accessing tax submission list API.

**Fix:** `.filter(user=self.request.user)`.

---

## FIN-002 | P1 — `CAProfileViewSet` exposes all CA profiles

**File:** `finance/views.py:13-16`

```python
queryset = CAProfile.objects.all()
```

No filter by `request.user`.

**Impact:** Any authenticated user can list/read all CA profiles.

**Fix:** Scope queryset or restrict to admin.

---

## FIN-003 | P2 — `DownloadTaxFilesView` wrong renter access on `Unit`

**File:** `finance/views.py:43-47`

```python
for p in properties:
    if p.renter and p.renter.rent_agreement:
```

**Model:** `Unit` has no direct `renter` FK (renters are reverse `unit.renters`).

**Impact:** `AttributeError` or never includes agreements.

**Fix:** Iterate `Renter.objects.filter(unit__owner=user)` or prefetch active renter.

---

## FIN-004 | P2 — `p.renter.police_verification` likely wrong relation

**File:** `finance/views.py:46`

- Police verification may be `PoliceVerification` model linked to renter, not a file on renter.

**Impact:** Missing files in tax ZIP.

---

## FIN-005 | P3 — `FileResponse(open(zip_file))` no context manager

**File:** `finance/views.py:51`

**Impact:** File handle leak under load.

---

## FIN-006 | P2 — `perform_create` on tax submission does not set `user`

**File:** `finance/views.py:26-27`

```python
def perform_create(self, serializer):
    serializer.save()
```

**Impact:** `user` may be null unless serializer/client sends it.

**Fix:** `serializer.save(user=self.request.user)`.
