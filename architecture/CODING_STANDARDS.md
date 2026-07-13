# Coding Standards

## Purpose
These standards apply to all code written during architecture phases. They ensure consistency, maintainability, and alignment with the architecture principles.

## Folder Conventions

### Django Apps
Each bounded context lives in a top-level Django app:
```
core/                    # Authentication, users, subscriptions
properties/              # Buildings, units, renters, rent records
finance/                 # Tax, CA profiles, financial reports
notification/            # Push, email, WhatsApp, voice
documents/               # Document generation and management
smartbot/                # AI chatbot and smart features
ai_assistant/            # AI-powered assistant services
referral_and_earn/       # Referral program
dashboard/               # Analytics and reporting
rentsecure_be/           # Project configuration and services
```

### Internal Structure
Within each app, prefer this layout:
```
app/
├── models/               # Domain models grouped by aggregate
├── services/             # Business logic
├── serializers/          # DRF serializers grouped by domain
├── views/                # Thin view classes
├── urls.py               # App URL configuration
├── admin.py              # Django admin configuration
├── signals.py            # Django signals (if needed)
├── utils.py              # App-specific utilities
├── constants.py          # App-specific constants
├── tests/                # Test suite
│   ├── test_services.py
│   ├── test_views.py
│   └── test_models.py
├── migrations/           # Django migrations
└── management/           # Management commands
```

## Naming Conventions

### General
- Use `snake_case` for files, directories, and modules
- Use `PascalCase` for classes
- Use `snake_case` for functions and variables
- Use `UPPER_SNAKE_CASE` for constants
- Use descriptive names; avoid abbreviations

### Services
- Suffix service classes with `Service` (e.g., `RentRecordService`)
- Group related services in modules by domain (e.g., `services/rent/`)
- One service class per file for complex services; group simple services in `services/__init__.py`

### Serializers
- Suffix with `Serializer` (e.g., `UnitSerializer`)
- Use `ReadSerializer` / `WriteSerializer` suffixes when read and write representations differ significantly
- Group serializers in `serializers/` subdirectories by domain

### Views
- Suffix with `ViewSet` or `View` (e.g., `UnitViewSet`, `HealthCheckView`)
- Use DRF generic viewsets where possible
- Keep view methods small (under 20 lines)

### Models
- Use singular nouns (e.g., `Renter`, not `Renters`)
- Foreign keys use singular model name + `_id` suffix (e.g., `unit_id`)
- Use `models.Model` subclasses in `models/` directory

## Service Naming
- Service class name describes the aggregate or use case (e.g., `RentPaymentService`)
- Method names are verbs (e.g., `process_payment`, `create_rent_record`)
- Service methods return domain objects or DTOs, never raw querysets to views

## Serializer Rules
- Serializers validate input and format output for transport
- No business logic in serializers
- Use `validate_<field>` for field-level validation
- Use `validate` for object-level validation only
- Keep serializers under 100 lines; extract validation to services if needed

## View Rules
- Views handle HTTP concerns only: auth, permissions, pagination, filtering
- Views call services; services contain business logic
- Views do not contain database queries directly (use services)
- Views do not contain conditional business rules
- Keep views under 50 lines; extract to services if needed

## Signal Rules
- Signals are allowed for side effects only (notifications, cache invalidation)
- No business logic in signals
- Signals must be connected in `apps.py` `ready()` method
- Document why each signal exists
- Prefer explicit service calls over signals when possible

## Management Command Rules
- Use `BaseCommand` from `django.core.management.base`
- Name commands with descriptive verbs (e.g., `recalculate_rent_balances`)
- Add `--dry-run` flag for destructive commands
- Log start, progress, and completion
- Handle `KeyboardInterrupt` gracefully

## Import Rules
- Import only from allowed layers per import-linter configuration
- Use absolute imports within the project
- Group imports: stdlib, third-party, local
- No circular imports; use dependency injection or late imports if needed
- Import-linter violations block CI

## Testing Rules
- Place tests in `tests/` directory within each app or in top-level `tests/`
- Name test files `test_<module>.py`
- Use pytest fixtures defined in `conftest.py`
- Unit test services in isolation
- Integration test views with DRF test client
- Contract tests verify boundaries between contexts
- Maintain ≥90% coverage
- Use hypothesis for property-based testing where applicable
