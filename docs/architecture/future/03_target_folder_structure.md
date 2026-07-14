# Target Folder Structure

This document defines the complete target repository layout for RentSecure.

---

## Complete Directory Tree

```
rentsecure_be/
├── apps/                          # Bounded contexts (Django apps)
│   ├── identity/                  # User authentication, authorization
│   ├── subscription/              # Plans, add-ons, feature flags
│   ├── property/                  # Buildings, units, renters
│   ├── rent/                      # Rent calculations, agreements
│   ├── payment/                   # Payment processing, webhooks
│   ├── notification/              # Email, push, WhatsApp, SMS
│   ├── document/                  # PDF generation, templates
│   ├── finance/                   # Tax, CA profiles, compliance
│   ├── referral/                  # Referral codes, bonuses
│   ├── ai/                        # SmartBot, AI assistant
│   └── dashboard/                 # Analytics, reporting
│
├── shared/                        # Cross-cutting utilities (no app imports)
│   ├── __init__.py
│   ├── constants.py               # App-wide constants
│   ├── domain_events.py           # Domain event definitions
│   ├── enums.py                   # Shared enumerations
│   ├── exceptions.py              # Base exception hierarchy
│   ├── interfaces.py              # Abstract base classes (ports)
│   ├── types.py                   # Shared type aliases
│   ├── utils.py                   # Generic utilities
│   ├── validators.py              # Shared validation logic
│   └── README.md
│
├── platform/                      # Infrastructure concerns
│   ├── __init__.py
│   ├── cache/                     # Cache adapters
│   │   ├── __init__.py
│   │   ├── interfaces.py          # CachePort
│   │   ├── locmem.py              # Django LocMem implementation
│   │   └── redis.py               # Redis implementation (Stage 2+)
│   ├── storage/                   # File storage adapters
│   │   ├── __init__.py
│   │   ├── interfaces.py          # StoragePort
│   │   ├── s3.py                  # S3 implementation
│   │   └── local.py               # Local storage (dev)
│   ├── search/                    # Search engine adapters
│   │   ├── __init__.py
│   │   ├── interfaces.py          # SearchPort
│   │   ├── postgres.py            # PostgreSQL full-text
│   │   └── opensearch.py          # OpenSearch (Stage 3+)
│   ├── queue/                     # Background job adapters
│   │   ├── __init__.py
│   │   ├── interfaces.py          # QueuePort
│   │   ├── cron.py                # Cron/systemd (Year 1)
│   │   └── celery.py              # Celery + Redis (Stage 2+)
│   ├── events/                    # Event bus infrastructure
│   │   ├── __init__.py
│   │   ├── bus.py                 # In-process event bus
│   │   ├── handlers.py            # Event handler registry
│   │   └── middleware.py          # Event middleware
│   └── di/                        # Dependency injection
│       ├── __init__.py
│       ├── container.py           # Service container
│       └── providers.py           # DI providers per context
│
├── config/                        # Django configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                # Shared settings
│   │   ├── development.py         # Local development
│   │   ├── production.py          # Production settings
│   │   ├── testing.py             # Test settings
│   │   └── ci.py                  # CI-specific settings
│   ├── urls.py                    # Root URL configuration
│   └── wsgi.py                    # WSGI application
│
├── scripts/                       # Operational scripts
│   ├── architecture_contract.py   # Import-linter + architecture tests
│   ├── seed_data.py               # Development data seeding
│   ├── backup_db.py               # Database backup utility
│   ├── restore_db.py              # Database restore utility
│   ├── generate_coverage_report.py
│   └── check_api_contracts.py
│
├── tools/                         # Development tools
│   ├── adr/                       # ADR templates and generators
│   ├── diagrams/                  # Diagram generation scripts
│   └── migrations/                # Migration helpers
│
├── tests/                         # Cross-cutting tests
│   ├── __init__.py
│   ├── factories.py               # Test factories (factory_boy)
│   ├── conftest.py                # Global pytest fixtures
│   ├── test_architecture_contract/ # Architecture contract tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_dependencies.py   # Import-linter tests
│   │   ├── test_layer_rules.py    # Layer boundary tests
│   │   └── test_validator.py
│   ├── test_api_contracts/        # API contract tests
│   ├── test_performance_benchmarks.py
│   ├── test_query_count.py
│   └── load/
│       ├── __init__.py
│       └── locustfile.py
│
├── docs/                          # Documentation
│   ├── architecture/
│   │   ├── future/                # Target architecture docs
│   │   │   ├── 01_architecture_vision.md
│   │   │   ├── 02_bounded_contexts.md
│   │   │   ├── 03_target_folder_structure.md
│   │   │   ├── 04_layer_rules.md
│   │   │   ├── 05_dependency_rules.md
│   │   │   ├── 06_module_responsibilities.md
│   │   │   ├── 07_domain_events.md
│   │   │   ├── 08_repository_pattern.md
│   │   │   ├── 09_service_layer.md
│   │   │   ├── 10_naming_conventions.md
│   │   │   ├── 11_migration_strategy.md
│   │   │   └── diagrams/
│   │   │       ├── context.mmd
│   │   │       ├── container.mmd
│   │   │       ├── component.mmd
│   │   │       ├── layers.mmd
│   │   │       ├── dependencies.mmd
│   │   │       ├── bounded_context.mmd
│   │   │       └── package.mmd
│   │   ├── adr/                   # Architecture Decision Records
│   │   │   ├── ADR-001_modular_monolith.md
│   │   │   ├── ADR-002_repository_pattern.md
│   │   │   ├── ...
│   │   │   └── ADR-015_api_versioning.md
│   │   ├── contracts/             # Cross-context contracts
│   │   └── README.md
│   ├── api/                       # API documentation
│   ├── business-rules/            # Business rule documentation
│   └── README.md
│
├── media/                         # User-uploaded files (dev only)
├── staticfiles/                   # Collected static files
├── .env.example                   # Environment variable template
├── .env                           # Environment variables (gitignored)
├── manage.py                      # Django management entry point
├── pyproject.toml                 # Project metadata and tool config
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Development dependencies
├── requirements-test.txt          # Test dependencies
├── pytest.ini                     # Pytest configuration
├── mypy.ini                       # MyPy configuration
├── ruff.toml                      # Ruff linter configuration
├── .import-linter                 # Import-linter configuration
├── docker-compose.yml             # Docker composition (optional)
├── Dockerfile                     # Container definition (optional)
├── README.md                      # Project README
└── CHANGELOG.md                   # Release notes
```

---

## Directory Purposes

### apps/
**Why it exists:** Contains all bounded contexts as Django apps. Each app is a self-contained domain module with its own models, services, repositories, and views.

**What belongs there:**
- All business domain code
- Models, services, repositories, serializers, views
- App-specific tests
- App-specific migrations
- App-specific templates and static files

**What never belongs there:**
- Cross-app business logic
- Shared utilities (belongs in `shared/`)
- Infrastructure code (belongs in `platform/`)
- Django project configuration (belongs in `config/`)

### shared/
**Why it exists:** Provides generic, reusable utilities that have no business logic. Acts as the shared kernel between bounded contexts.

**What belongs there:**
- Generic Python utilities (date helpers, string helpers)
- Base exception classes
- Shared enumerations
- Domain event base classes
- Abstract interface definitions (ports)
- Shared type definitions

**What never belongs there:**
- Any RentSecure-specific business logic
- Any Django app imports
- Any model definitions
- Any service implementations

### platform/
**Why it exists:** Encapsulates infrastructure concerns (cache, storage, search, queue) behind adapter interfaces. Allows swapping implementations without touching business logic.

**What belongs there:**
- Adapter interfaces (ports)
- Concrete implementations of adapters
- Event bus infrastructure
- Dependency injection container

**What never belongs there:**
- Business logic
- Domain models
- App-specific code

### config/
**Why it exists:** Django project configuration. Separated from apps to avoid circular imports and to make deployment environment management explicit.

**What belongs there:**
- Django settings (split by environment)
- Root URL configuration
- WSGI/ASGI applications
- Middleware configuration

**What never belongs there:**
- Business logic
- Models
- Views
- Services

### scripts/
**Why it exists:** Operational and development scripts that don't belong in Django management commands.

**What belongs there:**
- Architecture validation scripts
- Database backup/restore utilities
- Data seeding scripts
- Report generation scripts

**What never belongs there:**
- Business logic (use management commands in the relevant app)

### tools/
**Why it exists:** Developer tooling and generators that don't ship with the application.

**What belongs there:**
- ADR generators
- Diagram generators
- Migration helpers

**What never belongs there:**
- Runtime code

### tests/
**Why it exists:** Cross-cutting tests that don't belong to a single app, plus shared test infrastructure.

**What belongs there:**
- Architecture contract tests
- API contract tests
- Performance benchmarks
- Shared test factories
- Load testing scripts

**What never belongs there:**
- App-specific unit tests (belongs in `apps/<context>/tests/`)

### docs/
**Why it exists:** All documentation, organized by type and purpose.

**What belongs there:**
- Architecture documentation
- ADRs
- API documentation
- Business rules
- Runbooks

**What never belongs there:**
- Source code
- Generated files that belong in static files

---

## Internal App Structure

Every bounded context app follows this internal structure:

```
apps/<context>/
├── __init__.py
├── apps.py                    # Django app configuration
├── domain/                    # Pure domain layer (no Django imports)
│   ├── __init__.py
│   ├── entities/              # Domain entities (rich models)
│   ├── value_objects/         # Value objects (immutable)
│   ├── events/                # Domain events
│   ├── exceptions.py          # Domain-specific exceptions
│   └── policies/              # Domain policies (business rules)
├── infrastructure/            # Infrastructure implementations
│   ├── __init__.py
│   ├── repositories/          # Repository implementations
│   ├── persistence/           # Django model definitions
│   │   ├── __init__.py
│   │   ├── models.py          # Django ORM models
│   │   └── migrations/        # Auto-generated migrations
│   └── external/              # External service adapters
│       └── <adapter_name>.py
├── application/               # Application layer (use cases)
│   ├── __init__.py
│   ├── services/              # Application services
│   ├── commands/              # Command handlers (write)
│   ├── queries/               # Query handlers (read)
│   └── selectors/             # Read model selectors
├── interfaces/                # Presentation layer
│   ├── __init__.py
│   ├── serializers/           # DRF serializers
│   ├── views/                 # API views
│   ├── permissions/           # Permission classes
│   ├── urls.py                # App URL configuration
│   └── filters/               # DRF filter backends
├── infrastructure/            # Cross-cutting concerns
│   ├── __init__.py
│   ├── signals.py             # Django signals
│   ├── tasks.py               # Celery/cron tasks
│   └── management/            # Django management commands
│       └── commands/
└── tests/                     # App-specific tests
    ├── __init__.py
    ├── unit/                  # Unit tests
    ├── integration/           # Integration tests
    └── contract/              # Contract tests with other contexts
```

### Layer Rules Within an App

```
interfaces/  ──depends on──▶  application/  ──depends on──▶  domain/
     ▲                            │                            │
     │                            │                            │
     └────────────────────────────┘                            │
                          ▲                                    │
                          │                                    │
                          └────────  infrastructure/  ◀───────┘
                                     (implements domain interfaces)
```

**Rule:** Inner layers must never import from outer layers. `domain/` must never import from `infrastructure/`, `application/`, or `interfaces/`.

---

## Migration Mapping

| Current Location | Future Location | Notes |
|------------------|-----------------|-------|
| `core/models.py` | `apps/identity/infrastructure/persistence/models.py` | User, OTP models |
| `core/services/` | `apps/identity/application/services/` | Auth services |
| `core/views.py` | `apps/identity/interfaces/views/` | Auth views |
| `core/serializers.py` | `apps/identity/interfaces/serializers/` | Auth serializers |
| `properties/models/` | `apps/property/infrastructure/persistence/` | Property models |
| `properties/services/` | `apps/property/application/services/` | Property services |
| `properties/repositories/` | `apps/property/infrastructure/repositories/` | Repositories |
| `properties/policies/` | `apps/property/domain/policies/` | Domain policies |
| `properties/views/` | `apps/property/interfaces/views/` | Views |
| `properties/serializers/` | `apps/property/interfaces/serializers/` | Serializers |
| `notification/services/` | `apps/notification/application/services/` | Notification services |
| `notification/views.py` | `apps/notification/interfaces/views/` | Notification views |
| `finance/views.py` | `apps/finance/interfaces/views/` | Finance views |
| `finance/models.py` | `apps/finance/infrastructure/persistence/models.py` | Finance models |
| `documents/views.py` | `apps/document/interfaces/views/` | Document views |
| `smartbot/` | `apps/ai/` | Consolidate ai_assistant into ai |
| `ai_assistant/` | `apps/ai/` | Consolidate into ai |
| `referral_and_earn/` | `apps/referral/` | Rename |
| `dashboard/views.py` | `apps/dashboard/interfaces/views/` | Dashboard views |
| `rentsecure_be/services/` | `platform/` or context-specific | Split into contexts |
| `shared/` | `shared/` | Keep structure, add interfaces |
| `rentsecure_be/settings.py` | `config/settings/` | Split by environment |

---

*This structure represents the end state after all migration phases are complete. The migration moves files incrementally, never breaking production.*
