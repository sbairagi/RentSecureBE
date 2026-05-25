# RAG-002 — Tech Stack

**Metadata:** `id=RAG-002` | `tags=django,drf,python,dependencies` | `paths=requirements.txt,rentsecure_be/settings.py`

## Core framework

| Component | Version (requirements.txt) | Purpose |
|-----------|----------------------------|---------|
| Python | 3.12+ (tooling) | Runtime |
| Django | 4.2.30 | Web framework |
| Django REST Framework | 3.16.0 | REST API |
| djangorestframework-simplejwt | 5.5.0 | JWT auth |
| django-simple-history | 3.8.0 | Model audit trails |
| django-celery-beat | 2.9.0 | Scheduled tasks |
| fcm-django | (see requirements) | Push notifications |
| python-decouple | 3.8 (pin may say 3.9 — broken) | Environment variables |

## Payments and communications

- **Razorpay** — rent collection (payment links / orders)
- **Cashfree** — owner payouts
- **Twilio** — SMS OTP, WhatsApp
- **Leegality** — e-sign rent agreements
- **OpenAI** — SmartBot GPT replies

## Document and media

- **WeasyPrint** — PDF generation (invoices, reports)
- **AWS S3 / GCS** — optional file storage (env-configured)
- **gTTS** — voice note MP3 (`notification/services/voice_service.py`)

## Quality tooling

- pytest, coverage (90% gate in pytest.ini)
- black, ruff, pylint, mypy
- pre-commit, GitHub Actions workflows under `.github/workflows/`

## Database

- Default dev: SQLite (`DB_ENGINE` in `.env`)
- Production: PostgreSQL or MySQL via `DB_*` env vars

## Auth model

- Custom user: `core.User` (`AUTH_USER_MODEL = 'core.User'`)
- API default: `JWTAuthentication` on protected endpoints
