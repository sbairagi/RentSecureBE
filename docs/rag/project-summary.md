# RAG-001 — Project Summary

**Metadata:** `id=RAG-001` | `tags=overview,product,rental,SaaS` | `apps=all`

## What RentSecureBE is

RentSecureBE is a **Django REST Framework backend** for **rental property management** in India. Property **owners** manage portfolios (buildings, units, tenants), collect rent digitally, and receive payouts. **Renters** pay rent and view history via mobile/web clients.

## Primary users

| Role | Description |
|------|-------------|
| **Owner** | Landlord or property manager; creates portfolio, rent records, receives payouts |
| **Renter** | Tenant; pays rent, optional KYC/onboarding |
| **CA (Chartered Accountant)** | Optional; receives tax document bundles from owners |

## Core capabilities

- Portfolio: buildings → units → renters → caretakers
- Monthly **rent records** with Razorpay payment links
- Owner **payouts** via Cashfree to registered bank accounts
- **Subscription tiers** (Free / Pro / Elite) with feature limits
- Notifications: WhatsApp, email, push (FCM), voice notes (gTTS)
- Rent agreements: Leegality e-sign, PDF generation
- **SmartBot**: GPT + keyword intents for owners
- Referral program on signup

## Repository name and entrypoint

- Repo folder: `RentSecureBE`
- Django project package: `rentsecure_be`
- Manage command: `python manage.py`
- Settings: `rentsecure_be/settings.py`
- Root URLs: `rentsecure_be/urls.py`

## Documentation map (for AI)

| Need | Path |
|------|------|
| Architecture chunks | `docs/rag/` (this folder) |
| Business policy | `docs/business-rules/` |
| Bugs | `docs/bugs/` |
| Gaps (policy vs code) | `docs/business-gaps/` |
