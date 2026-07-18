# RentSecureBE

![Django](https://img.shields.io/badge/Django-5.2-green)
![DRF](https://img.shields.io/badge/DRF-3.16-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-blue)
![AWS](https://img.shields.io/badge/AWS-EC2-orange)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-black)

> **Enterprise-grade Django backend for property management, rent collection, and financial operations.**

---

## Architecture

> Diagrams are generated automatically by the `uml.yml` workflow and published as artifacts.

![CI/CD Pipeline](docs/diagrams/generated/infrastructure/cicd-pipeline.puml)
![C4 Context](docs/diagrams/generated/c4/c4-context.puml)
![C4 Container](docs/diagrams/generated/c4/c4-container.puml)


## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 5.2 |
| API | Django REST Framework |
| Auth | JWT (SimpleJWT) |
| Database | PostgreSQL (Production), SQLite (Development) |
| Cache | Django Local Memory Cache (Year 1), Redis (Stage 2) |
| Background Tasks | Cron + Management Commands (Year 1), Celery (Stage 2) |
| Storage | AWS S3 |
| Deployment | AWS EC2 + Nginx + Gunicorn |
| CI/CD | GitHub Actions |
| Code Quality | SonarCloud, import-linter |
| Notifications | Email, FCM Push, In-App (Year 1), WhatsApp/SMS (Stage 2) |

## Project Structure

```
rentsecure_be/
├── core/                    # Authentication, users, subscriptions
├── properties/              # Buildings, units, renters, rent records
├── finance/                 # Tax, CA profiles, financial reports
├── notification/            # Push, email, WhatsApp, voice notifications
├── documents/               # Document generation and management
├── smartbot/                # AI chatbot and smart features
├── ai_assistant/            # AI-powered assistant services
├── referral_and_earn/       # Referral program
├── dashboard/               # Analytics and reporting
├── rentsecure_be/           # Project configuration and services
└── tools/                   # CI/CD and development tools
```

## CI/CD Pipeline

The project uses a comprehensive CI/CD pipeline with multiple stages:

1. **Lint**: Black, Ruff, Pylint, Mypy, Vulture
2. **Test**: Pytest with 4-way sharding, coverage ≥90%
3. **Architecture**: Import-linter validation, dependency graphs
4. **Security**: Bandit, Semgrep, Pip-audit, Trivy, Gitleaks
5. **Quality**: SonarCloud quality gate
6. **Deploy Readiness**: Environment validation
7. **Deploy**: EC2 SSH deployment with Sentry tracking

See [docs/ci-cd-pipeline.md](docs/ci-cd-pipeline.md) for details.

## UML Diagrams

Auto-generated diagrams are available in:

- [docs/uml/](docs/uml/) — PlantUML and Mermaid diagrams
- [docs/diagrams/](docs/diagrams/) — C4, flow, infrastructure diagrams

## Documentation

- [Architecture Contract](docs/architecture-contract.md)
- [CI/CD Governance](docs/governance.md)
- [Business Rules](docs/business-rules/README.md)
- [AI Governance](docs/ai-governance/README.md)
- [ADR Index](docs/architecture/adr/README.md)

## Setup

```bash
# Clone repository
git clone <repository-url>
cd RentSecureBE

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest properties/tests/test_unit_views.py

# Run with hypothesis
pytest tests/test_properties_hypothesis.py
```

## Feature Flags

Optional integrations are controlled via feature flags:

| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_RAZORPAY` | False | Razorpay payment integration |
| `ENABLE_CASHFREE` | False | Cashfree payment integration |
| `ENABLE_WHATSAPP` | False | WhatsApp notifications |
| `ENABLE_VOICE` | False | Voice note generation |
| `ENABLE_OPENAI` | False | OpenAI AI features |
| `ENABLE_LEEGALITY` | False | Leegality e-signature |
| `ENABLE_EMAIL` | True | Email notifications |
| `ENABLE_PUSH_NOTIFICATION` | True | Push notifications |

## Architecture Diagrams

> Diagrams are generated automatically by CI. See the [UML Diagrams](docs/uml/) and [Diagrams](docs/diagrams/) sections for artifact links after CI runs.

- [PlantUML Diagrams](docs/uml/)
- [Mermaid Diagrams](docs/uml/)
- [C4 Diagrams](docs/diagrams/generated/c4/)
- [Domain Diagrams](docs/uml/generated/domain/)
- [Flow Diagrams](docs/diagrams/generated/flows/)
- [Infrastructure Diagrams](docs/diagrams/generated/infrastructure/)
- [DDD Diagrams](docs/uml/generated/ddd/)

## Contributing

See [docs/ai-governance/AI-Contribution-Guide.md](docs/ai-governance/AI-Contribution-Guide.md) for contribution guidelines.

## License

MIT
