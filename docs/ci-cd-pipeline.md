# CI/CD Pipeline & UML Overview

> **Project:** RentSecureBE — Production-Grade Django Backend
> **Stack:** Django 5.2 / DRF / PostgreSQL / AWS EC2 / Cashfree
> **Pipeline Version:** 2.3.0

---

## Part 1: CI/CD Pipeline Flow Diagram

```mermaid
flowchart LR
    %% ─── Node Definitions ──────────────────────────────────────────────────────

    S1["<b>🛠  Setup & Code Quality</b><br/><br/>• Checkout Code<br/>• Setup Python 3.12<br/>• Cache pip dependencies<br/>• Pre-commit + Black + Ruff<br/>• Pylint + Mypy (strict)<br/>• Vulture Dead Code Detection"]

    S2["<b>🧪  Tests</b><br/><br/>• Pytest + Coverage (≥90%, 4-way sharded)<br/>• API Contract Tests<br/>• Django System & Migration Checks"]

    S3["<b>📐  Architecture</b><br/><br/>• Import Linter Validation<br/>• Layered Architecture Check"]

    S4["<b>🔒  Security Fast</b><br/><br/>• Bandit (matrix per app)<br/>• Semgrep (OWASP + Django)<br/>• Pip-audit Dependencies<br/>• Trivy FS Vulnerability<br/>• Gitleaks Secret Scan"]

    S5["<b>📊  Quality Gate</b><br/><br/>• SonarCloud Analysis<br/>• Quality Gate Check<br/>• Wait for Gate Status<br/>• Coverage Report Upload"]

    S6["<b>🚀  Deploy Readiness</b><br/><br/>• Environment Variable Validation<br/>• Deployment Script Verification"]

    D["<b>🚀  Deploy</b><br/><br/>• Build Docker Image<br/>• Push to Container Registry<br/>• Deploy to AWS EC2<br/>• Sentry Release & Deploy"]

    %% ─── Edges ─────────────────────────────────────────────────────────────────
    S1 --> S2
    S1 --> S3
    S1 --> S4
    S2 --> S5
    S3 --> S5
    S5 --> S6
    S6 --> D

    %% ─── Styling ───────────────────────────────────────────────────────────────
    classDef setup     fill:#E3F2FD,stroke:#1565C0,stroke-width:3px,color:#0D47A1,rx:12px,ry:12px
    classDef quality   fill:#FFF3E0,stroke:#E65100,stroke-width:3px,color:#BF360C,rx:12px,ry:12px
    classDef test      fill:#E8F5E9,stroke:#2E7D32,stroke-width:3px,color:#1B5E20,rx:12px,ry:12px
    classDef arch      fill:#E0F7FA,stroke:#00838F,stroke-width:3px,color:#006064,rx:12px,ry:12px
    classDef security  fill:#FFEBEE,stroke:#C62828,stroke-width:3px,color:#B71C1C,rx:12px,ry:12px
    classDef gate      fill:#FCE4EC,stroke:#AD1457,stroke-width:3px,color:#880E4F,rx:12px,ry:12px
    classDef deploy    fill:#E8F5E9,stroke:#1B5E20,stroke-width:3px,color:#0D47A1,rx:12px,ry:12px

    class S1 setup
    class S2,S3 test
    class S4 security
    class S5 gate
    class S6 deploy
    class D deploy
```

### Pipeline Summary (from `.github/workflows/ci.yml`)

| # | Stage | Key Jobs | Runtime Source |
|---|-------|----------|----------------|
| 1 | **Setup & Code Quality** | `pre-commit, black, ruff, pylint, mypy, vulture` | Measured by CI Metrics (`ci-metrics.yml`) |
| 2 | **Tests** | `pytest + coverage (4-way sharded)`, `API contract tests`, `Django checks` | Measured by CI Metrics |
| 3 | **Architecture** | `import-linter` | Measured by CI Metrics |
| 4 | **Security Fast** | `bandit (matrix)`, `semgrep`, `pip-audit`, `trivy`, `gitleaks`, `dependency-review` | Measured by CI Metrics |
| 5 | **Quality Gate** | `sonarcloud` analysis + quality gate wait | Measured by CI Metrics |
| 6 | **Deploy Readiness** | `env validation`, `script verification` | Measured by CI Metrics |
| 7 | **Deploy** | `deploy.yml`: EC2 SSH, Docker, Sentry release | Measured by CI Metrics |

> **Note:** Runtimes are collected automatically via `.github/workflows/ci-metrics.yml` using the GitHub Actions API (last 30 successful runs). PR pipeline target is ≤15 minutes. Deep validation (hypothesis, mutation, load testing, codeql, scorecard, SBOM scanning) runs nightly/weekly.

---

### Optional Enhancements

| Enhancement | Description |
|-------------|-------------|
| ⚡ **Parallel Job Execution** | Lint, Security, and Test workflows run concurrently to reduce total wall-clock time. |
| 🐍 **Matrix Testing** | Python 3.12 (standardized runtime). |
| 💾 **Aggressive Caching** | pip cache (`~/.cache/pip`) and pre-commit cache (`~/.cache/pre-commit`) cut CI time by ~40%. |
| 📦 **Build Artifacts** | Coverage reports, Locust HTML reports, and mutmut results persist as downloadable artifacts. |
| 🔔 **Notifications** | Slack / Email alerts on pipeline failure, deploy success, or quality gate breach. |
| 🛡️ **Environment Protection** | Require manual approval before deploying to production. |
| ✅ **Manual Approval Gate** | Production deploy gates enforce a designated approver sign-off. |
| 📈 **Performance Regression Check** | Automated benchmark comparison against last-known-good run. |

---

## Part 2: What is UML?

<div style="border: 2px solid #1565C0; border-radius: 12px; padding: 20px; background: #F8F9FA;">

**UML (Unified Modeling Language)** is a standardized visual modeling language used in software engineering to specify, visualize, construct, and document the artifacts of a software system. It helps developers, architects, and stakeholders understand the system's structure, behavior, and deployment through a rich set of diagram types.

**Why we use it:**
- 📌 **Communicate architecture** across technical and non-technical teams
- 📌 **Document design decisions** before implementation
- 📌 **Verify consistency** between code and design
- 📌 **Onboard new engineers** faster with visual context

</div>

---

## Part 3: Types of UML Diagrams

| # | Diagram Type | Purpose |
|---|--------------|---------|
| 1 | **Use Case Diagram** | Captures system functionality from an end-user perspective — shows actors, use cases, and boundaries. |
| 2 | **Class Diagram** | Models the static structure: classes, attributes, methods, and relationships (inheritance, associations, dependencies). |
| 3 | **Sequence Diagram** | Shows object interactions arranged in time sequence — message flow between actors and system components. |
| 4 | **Activity Diagram** | Models workflow or business process steps with decision nodes, parallel forks, and joins. |
| 5 | **State Machine Diagram** | Describes the lifecycle of an object — states, transitions, events, and triggers. |
| 6 | **Component Diagram** | Illustrates high-level system components and their interface dependencies. |
| 7 | **Deployment Diagram** | Maps software artifacts to physical or cloud hardware nodes (servers, containers, storage). |
| 8 | **Communication Diagram** | Focuses on object collaboration links and messages (structural view of interactions). |

---

## Part 4: Example UML Diagrams for RentSecureBE

### 4.1 — Class Diagram (Core Domain Model)

```mermaid
classDiagram
    %% ── User & Profile ─────────────────────────────────────────────────────────
    class User {
        +id: int
        +email: string
        +full_name: string
        +phone: string
        +is_investor: boolean
        +is_phone_verified: boolean
        +whatsapp_number: string
        +register()
        +login()
    }

    class UserProfile {
        +user: User
        +language_preference: string
        +notification_prefs: JSON
        +timezone: string
        +update()
    }

    %% ── Property ───────────────────────────────────────────────────────────────
    class Building {
        +id: int
        +name: string
        +address_line: string
        +city: string
        +owner: User
        +is_archived: boolean
        +created_at: datetime
        +get_active_units()
    }

    class Unit {
        +id: int
        +unit: string
        +unit_type: string
        +status: string
        +is_vacant: boolean
        +building: Building
        +owner: User
        +rent_due_date: date
        +monthly_rent: decimal
        +vacate()
    }

    class UnitImage {
        +id: int
        +unit: Unit
        +image: ImageField
        +caption: string
        +is_primary: boolean
        +uploaded_at: datetime
    }

    %% ── Rental ─────────────────────────────────────────────────────────────────
    class Renter {
        +id: int
        +name: string
        +email: string
        +phone: string
        +rent_amount: decimal
        +start_date: date
        +end_date: date
        +status: string
        +unit: Unit
        +user: User
        +is_active: boolean
        +send_notice()
        +terminate()
    }

    class AgreementRevocationLog {
        +id: int
        +renter: Renter
        +revoked_by: User
        +reason: string
        +revoked_at: datetime
    }

    class RentRecord {
        +id: int
        +amount: decimal
        +status: string
        +payment_method: string
        +paid_on: date
        +due_date: date
        +transaction_id: string
        +payout_status: string
        +unit: Unit
        +renter: Renter
        +generate_invoice()
        +mark_as_paid()
        +retry_payout()
    }

    class ExtraCharge {
        +id: int
        +renter: Renter
        +description: string
        +amount: decimal
        +charge_type: string
        +created_at: datetime
        +is_paid: boolean
    }

    %% ── Finance ────────────────────────────────────────────────────────────────
    class OwnerBankDetails {
        +owner: User
        +bank_account_number: string
        +ifsc_code: string
        +bank_account_verified: boolean
        +upi_id: string
        +process_payout()
    }

    %% ── Subscription ───────────────────────────────────────────────────────────
    class SubscriptionPlan {
        +id: int
        +name: string
        +monthly_price: decimal
        +yearly_price: decimal
        +features: JSON
        +addon_limits: JSON
        +is_active: boolean
    }

    class UserSubscription {
        +user: User
        +plan: SubscriptionPlan
        +start_date: date
        +end_date: date
        +is_active: boolean
        +auto_renew: boolean
        +is_expired()
    }

    class FeatureUsageLimit {
        +user: User
        +feature_key: string
        +used_count: int
        +limit_count: int
        +reset_at: datetime
        +is_exhausted()
    }

    %% ── Notifications ──────────────────────────────────────────────────────────
    class Notification {
        +id: int
        +user: User
        +title: string
        +message: text
        +is_read: boolean
        +created_at: datetime
        +mark_as_read()
    }

    class DeviceToken {
        +user: User
        +token: string
        +platform: string
    }

    %% ── Relationships ──────────────────────────────────────────────────────────
    User "1" --> "1" UserProfile : extends
    User "1" --> "*" Building : owns
    Building "1" --> "*" Unit : contains
    Unit "1" --> "*" UnitImage : has images
    Unit "*" --> "1" Renter : houses
    User "1" --> "1" Renter : becomes
    Renter "1" --> "*" AgreementRevocationLog : logs
    Unit "1" --> "*" RentRecord : generates
    Renter "1" --> "*" RentRecord : pays
    Renter "1" --> "*" ExtraCharge : incurs
    User "1" --> "1" OwnerBankDetails : receives payout via
    User "1" --> "1" UserSubscription : holds
    UserSubscription "*" --> "1" SubscriptionPlan : references
    User "1" --> "*" FeatureUsageLimit : tracks
    User "1" --> "*" Notification : receives
    User "1" --> "*" DeviceToken : registered on
```

---

### 4.2 — Sequence Diagram: Rent Payment & Payout Flow

```mermaid
sequenceDiagram
    %% ── Participants ───────────────────────────────────────────────────────────
    actor Owner
    actor Renter
    participant API as RentRecord API
    participant Cashfree as Cashfree<br/>(PG + Payout)
    participant DB as Database
    participant Notify as Notification<br/>Service
    participant PDF as Invoice<br/>Engine (Celery)

    %% ── 1. Create & Share ─────────────────────────────────────────────────────
    Owner->>API: POST /api/properties/rent-records/
    API->>DB: Save RentRecord (status=pending)
    API->>Cashfree: Create Payment Link
    Cashfree-->>API: payment_link_url
    API-->>Owner: Return RentRecord + payment link

    Owner->>Renter: Share payment link

    %% ── 2. Payment ────────────────────────────────────────────────────────────
    Renter->>Cashfree: Pay via payment link
    Cashfree->>API: Webhook: payment.success
    API->>DB: Update RentRecord (status=paid, paid_on=now)
    API->>Notify: Send Payment Confirmation to Owner & Renter
    API->>PDF: Enqueue async invoice generation
    PDF-->>API: Invoice PDF URL (callback)

    %% ── 3. Payout ─────────────────────────────────────────────────────────────
    par Payout Processing
        API->>Cashfree: POST /payout — trigger owner payout
        Cashfree-->>API: payout_id (initiated)
        API->>DB: Update payout_status → processing

        Cashfree->>API: Webhook: payout.success
        API->>DB: Update payout_status → completed
        API->>Notify: Payout success alert to Owner
    end

    %% ── 4. Failure & Retry ─────────────────────────────────────────────────────
    alt Payout Failed
        Owner->>API: POST /api/owner/retry_payout/
        API->>Cashfree: Re-trigger payout
        Cashfree-->>API: payout result
        API->>DB: Update payout_status
        API->>Notify: Retry result notification to Owner
    end

    %% ── 5. Reconciliation ─────────────────────────────────────────────────────
    Note over API,DB: Daily cron: reconcile pending payouts with Cashfree ledger
```

---

### 4.3 — Sequence Diagram: Subscription Enforcement Flow

```mermaid
sequenceDiagram
    actor User
    participant API as Feature API
    participant Enforcer as FeatureUsage<br/>Enforcer
    participant DB as Database
    participant Cache as Redis Cache

    User->>API: Request feature access (e.g., add unit)
    API->>Enforcer: check_feature_access(user, feature_key)

    Enforcer->>Cache: GET feature_usage:{user_id}:{key}
    alt Cache Hit
        Cache-->>Enforcer: current_usage + limit
    else Cache Miss
        Enforcer->>DB: SELECT count from feature_usage
        DB-->>Enforcer: usage data
        Enforcer->>Cache: SET with TTL
    end

    alt Plan Expired
        Enforcer-->>API: BLOCKED — subscription expired
        API-->>User: ❌ 402 Payment Required
    else Limit Exceeded
        Enforcer-->>API: BLOCKED — limit reached
        API-->>User: ❌ 429 Too Many Requests
    else Within Limit
        Enforcer->>DB: Increment usage count
        Enforcer-->>API: ALLOWED
        API-->>User: ✅ Success
    end

    Note over Cache,DB: Redis TTL = 5 min; DB writes are synchronous for accuracy.
```

---

### 4.4 — Deployment Diagram (Simplified AWS Architecture)

```mermaid
flowchart TD
    subgraph Client["🌐 Clients"]
        A["📱 React Native App<br/>(Expo Router)"]
        B["🌍 Web Browser"]
    end

    subgraph AWS["☁️ AWS Cloud"]
        subgraph Network["🕸️ Networking"]
            LB["🔁 Application<br/>Load Balancer"]
            CDN["⚡ CloudFront /<br/>Route 53"]
        end

        subgraph Compute["🖥️ Compute"]
            EC2["🖧 EC2 Instance<br/>(Django + Gunicorn)"]
            Worker["⚙️ Celery Worker<br/>(Background Tasks)"]
            Beat["⏰ Celery Beat<br/>(Cron / Scheduler)"]
        end

        subgraph Storage["💾 Storage"]
            RDS["🗄️ PostgreSQL<br/>(Aurora / RDS)"]
            Redis["⚡ Redis / ElastiCache<br/>(Cache + Queue)"]
            S3["📦 S3 Bucket<br/>(Media, PDFs, Logs)"]
        end
    end

    subgraph External["🔗 External Services"]
        CF["💳 Cashfree<br/>(PG + Payouts)"]
        Twilio["💬 Twilio / Interakt<br/>(WhatsApp)"]
        Sentry["📊 Sentry<br/>(Error Tracking)"]
        Sonar["📈 SonarCloud<br/>(Code Quality)"]
        GitHub["🐙 GitHub Actions<br/>(CI/CD)"]
    end

    %% Connections
    A --> LB
    B --> CDN --> LB
    LB --> EC2
    EC2 --> Worker
    EC2 --> Beat
    EC2 <--> RDS
    EC2 <--> Redis
    Worker <--> Redis
    Worker --> S3
    EC2 --> CF
    Worker --> CF
    EC2 --> Twilio
    Worker --> Sentry
    GitHub --> EC2
    GitHub --> Sonar

    classDef client fill:#E3F2FD,stroke:#1565C0,stroke-width:2px
    classDef aws fill:#FFF8E1,stroke:#F57F17,stroke-width:2px
    classDef network fill:#E0F7FA,stroke:#00838F,stroke-width:2px
    classDef compute fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px
    classDef storage fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    classDef external fill:#FFEBEE,stroke:#C62828,stroke-width:2px

    class A,B client
    class LB,CDN network
    class EC2,Worker,Beat compute
    class RDS,Redis,S3 storage
    class CF,Twilio,Sentry,Sonar,GitHub external
```

---

*This documentation reflects the production-grade CI/CD architecture and domain model for the RentSecureBE project. Diagrams are rendered with Mermaid.js and can be viewed on any GitHub repository or Mermaid-compatible Markdown renderer.*
