# RAG-023 — Development Runbook

**Metadata:** `id=RAG-023` | `tags=setup,migrate,test,runserver`

## Prerequisites

- Python 3.12+
- Virtualenv recommended

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Database

```bash
python manage.py migrate
python manage.py createsuperuser   # optional
```

## Seed subscription (required for API creates)

Django shell example:

```python
from core.models import SubscriptionPlan, PlanFeatureLimit, UserSubscription
from django.contrib.auth import get_user_model
User = get_user_model()
free, _ = SubscriptionPlan.objects.get_or_create(
    name='free', defaults={'monthly_price': 0, 'yearly_price': 0, 'is_active': True}
)
for key, val in [('max_buildings','3'),('max_units','10'),('max_renters','20')]:
    PlanFeatureLimit.objects.get_or_create(plan=free, feature_key=key, defaults={'value': val})
```

## Run server

```bash
python manage.py runserver
```

## Tests

```bash
pytest --no-cov          # avoid 90% coverage failure
pytest properties/tests/ -q --no-cov
```

## OTP in development

`DEBUG=True` → OTP printed to console, not sent via Twilio.

## Pre-commit

```bash
git config core.hooksPath .githooks
pre-commit install --install-hooks
```

## AI: common dev pitfalls

- Fresh DB without plans → 403 on building create
- Signals unwired → no auto subscription
- Webhooks need public URL + correct secrets for integration tests
