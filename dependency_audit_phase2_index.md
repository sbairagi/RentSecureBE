# RentSecureBE – Dependency Hygiene Audit (Phase 2) – INDEX

**Status:** ANALYSIS ONLY – No changes applied
**Date:** 2026-05-06
**Auditor:** Principal Staff Engineer / Dependency Governance Reviewer

---

## Audit Documents

The full audit is split across the following files:

| Part | File | Contents |
|---|---|---|
| **1** | `dependency_audit_phase2.md` | Executive Summary, Methodology, Full Dependency Inventory (217 packages, P/D/T/U/? classification) |
| **2** | `dependency_audit_phase2_part2.md` | Classification Summary, Production Package List, Possibly Unused Packages with evidence (high/medium/low confidence) |
| **3** | `dependency_audit_phase2_part3.md` | Security Review (unmaintained, deprecated, risky, duplicate, upgrade candidates), Phase 2A & 2B Migration Plans |
| **4** | `dependency_audit_phase2_part4.md` | Phase 2C Upgrade Roadmap, Proposed `requirements.txt`, Proposed `requirements-dev.txt`, Key Risks, Sign-off Checklist, Out of Scope |

---

## Quick Findings

| Metric | Value |
|---|---|
| Total packages in `requirements.txt` | **217** |
| Production-only (P) | **16** (7.4%) |
| Development-only (D) | **2** (0.9%) |
| Transitive (T) – should NOT be pinned at top level | **158** (72.8%) |
| Possibly Unused (U) | **33** (15.2%) |
| Unknown (?) | **2** (0.9%) |
| Risky (subset of U) | **1** (instagram-private-api) |

---

## Top 5 Action Items (post-approval)

1. **Remove `instagram-private-api==1.6.0.0`** – unofficial, reverse-engineered, unused (Phase 2B.1)
2. **Remove `django-rest-auth==0.9.5`** – deprecated since 2019, replaced by simplejwt (Phase 2B.2)
3. **Remove `Flask==3.1.1`, `fpdf`, `fpdf2`, `selenium`, `SQLAlchemy`, `pandas`, `PyMySQL`, `instaloader`** – all unused (Phase 2B.3–2B.5)
4. **Decide celery architecture** – either define `rentsecure_be/celery.py` or remove celery stack (Phase 2B.8)
5. **Split `requirements.txt` and `requirements-dev.txt`** (Phase 2A, low risk, additive)

---

## No Changes Were Made

- ❌ No application code modified
- ❌ No database models modified
- ❌ No git commits created
- ❌ No packages removed from `requirements.txt`
- ❌ No workflows modified
- ❌ No migrations touched
- ✅ Audit documents written to the project root for review

---

## Awaiting Approval

This audit is **analysis-only**. Please review the four parts and approve
the migration plan (or request changes) before any modifications are applied.
