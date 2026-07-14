# 01 Dependency Graph

## Package Dependency Graph

```mermaid
graph TD
    subgraph "Project Root"
        A[core]
        B[properties]
        C[smartbot]
        D[finance]
        E[notification]
        F[documents]
        G[referral_and_earn]
        H[ai_assistant]
        I[dashboard]
        J[rentsecure_be]
        K[shared]
        L[management]
        M[tests]
        N[tools]
        O[scripts]
    end

    A -->|imports| B
    A -->|imports| E
    A -->|imports| G
    A -->|imports| K
    A -->|imports| J

    B -->|imports| A
    B -->|imports| E
    B -->|imports| J

    C -->|imports| B
    C -->|imports| E
    C -->|imports| J

    D -->|imports| A
    D -->|imports| B
    D -->|imports| J

    E -->|imports| B
    E -->|imports| J

    F -->|imports| A
    F -->|imports| B

    G -->|imports| J

    H -->|imports| A
    H -->|imports| B
    H -->|imports| E
    H -->|imports| C

    I -->|imports| B
    I -->|imports| C

    J -->|imports| A
    J -->|imports| B
    J -->|imports| E

    L -->|imports| A
    L -->|imports| B
    L -->|imports| E
    L -->|imports| J

    M -->|imports| A
    M -->|imports| B
    M -->|imports| J
    M -->|imports| O
    M -->|imports| K

    N -->|imports| N

    O -->|imports| A
```

**Evidence:** Derived from AST analysis of 340 Python files. Cross-app imports: 205.

## App Dependency Graph (Simplified)

```
core
├── properties
├── notification
├── referral_and_earn
├── shared
└── rentsecure_be

properties
├── core
├── notification
└── rentsecure_be

smartbot
├── properties
├── notification
└── rentsecure_be

finance
├── core
├── properties
└── rentsecure_be

notification
├── properties
└── rentsecure_be

documents
├── core
└── properties

ai_assistant
├── properties
├── core
├── notification
└── smartbot

dashboard
├── properties
└── smartbot
```

## Module Dependency Graph (Top-Level)

| Module | Imports From | Imported By |
|--------|-------------|-------------|
| `properties.models` | - | 74 modules |
| `core.models` | `rentsecure_be.type_compat` | 63 modules |
| `rentsecure_be.type_compat` | stdlib | 36 modules |
| `notification.services.whatsapp_service` | stdlib, twilio, boto3 | 21 modules |
| `core.views` | core.services, notification.services, properties.models, rentsecure_be | 3 modules |
| `properties.signals` | notification.models, notification.services, properties.models, properties.scheduler, properties.services, properties.utils | 3 modules |
| `rentsecure_be.services.cashfree_service` | core.models, notification.services, properties.models, rentsecure_be.utils | 6 modules |
| `properties.utils.utils` | core.models, notification.services, properties.models, properties.feature_enforcer | 3 modules |
| `notification.utils` | stdlib | 6 modules |
| `notification.models` | django | 6 modules |

## High-Level Architecture Diagram

```mermaid
flowchart LR
    subgraph "Django Apps"
        direction TB
        CORE[core]
        PROPS[properties]
        SMART[smartbot]
        FIN[finance]
        NOTIF[notification]
        DOCS[documents]
        REF[referral_and_arnn]
        AI[ai_assistant]
        DASH[dashboard]
    end

    subgraph "Infrastructure"
        RBE[rentsecure_be]
        SHARED[shared]
    end

    subgraph "Orchestration"
        MGMT[management.commands]
        TESTS[tests]
        TOOLS[tools]
        SCRIPTS[scripts]
    end

    CORE --> PROPS
    CORE --> NOTIF
    CORE --> REF
    CORE --> SHARED
    CORE --> RBE

    PROPS --> CORE
    PROPS --> NOTIF
    PROPS --> RBE

    SMART --> PROPS
    SMART --> NOTIF
    SMART --> RBE

    FIN --> CORE
    FIN --> PROPS
    FIN --> RBE

    NOTIF --> PROPS
    NOTIF --> RBE

    DOCS --> CORE
    DOCS --> PROPS

    AI --> CORE
    AI --> PROPS
    AI --> NOTIF
    AI --> SMART

    DASH --> PROPS
    DASH --> SMART

    REF --> RBE

    MGMT --> CORE
    MGMT --> PROPS
    MGMT --> NOTIF
    MGMT --> RBE

    TESTS --> CORE
    TESTS --> PROPS
    TESTS --> RBE
    TESTS --> SCRIPTS

    TOOLS --> TOOLS

    SCRIPTS --> CORE
```

## Core Dependency Graph

```mermaid
graph TD
    subgraph "core"
        CM[core.models]
        CV[core.views]
        CS[core.services]
        CS_AUTH[core.services.auth_service]
        CS_BANK[core.services.bank_details_service]
        CS_OTP[core.services.otp_service]
        CS_OWNER[core.services.owner_reporting_service]
        CS_PWD[core.services.password_service]
        CS_REF[core.services.referral_service]
        CS_SUB[core.services.subscription_service]
        CS_UL[core.services.usage_limit_service]
        CS_BASE[core.services.base]
        CSIG[core.signals]
    end

    subgraph "External"
        PROPS[properties]
        NOTIF[notification]
        REF[referral_and_earn]
        SHARED[shared]
        RBE[rentsecure_be]
    end

    CM --> RBE
    CS_BANK --> PROPS
    CS_BANK --> RBE
    CS_OWNER --> PROPS
    CS_REF --> REF
    CS_REF --> SHARED
    CS_UL --> CS_SUB
    CV --> CS
    CV --> NOTIF
    CV --> PROPS
    CV --> RBE
    CV --> SHARED
    CS_AUTH --> CM
    CS_AUTH --> CS_BASE
    CS_BANK --> CM
    CS_BANK --> CS_BASE
    CS_OTP --> CS_BASE
    CS_OTP --> SHARED
    CS_PWD --> CS_BASE
    CS_SUB --> CM
    CS_SUB --> CS_BASE
    CSIG --> CM
```

## Properties Dependency Graph

```mermaid
graph TD
    subgraph "properties"
        PM[properties.models]
        PV[properties.views]
        PS[properties.services]
        PSER[properties.serializers]
        PSIG[properties.signals]
        PAD[properties.admin]
        PREP[properties.repositories]
        PPOL[properties.policies]
        PCONST[properties.constants]
        PFEAT[properties.feature_enforcer]
    end

    subgraph "External"
        CORE[core]
        NOTIF[notification]
        RBE[rentsecure_be]
    end

    PM --> CORE
    PM --> RBE
    PV --> CORE
    PV --> NOTIF
    PV --> RBE
    PS --> PM
    PS --> NOTIF
    PSER --> RBE
    PSIG --> NOTIF
    PSIG --> PM
    PSIG --> PS
    PSIG --> PFEAT
    PFEAT --> CORE
    PREP --> PM
    PPOL --> PM
```

## Notification Dependency Graph

```mermaid
graph TD
    subgraph "notification"
        NM[notification.models]
        NV[notification.views]
        NS[notification.services]
        NS_WA[notification.services.whatsapp_service]
        NS_SMS[notification.services.sms_service]
        NS_VOICE[notification.services.voice_service]
        NS_VN[notification.services.voice_note_service]
        NS_COMM[notification.services.communication]
        NS_NOTIF[notification.services.notifications]
        NS_RENT[notification.services.rent_notify_service]
        NS_EC[notification.services.extra_charge_reminders]
        NS_SCHED[notification.services.schedule_reminders]
        NS_LATE[notification.services.late_fees_notify_service]
        NUTIL[notification.utils]
    end

    subgraph "External"
        PROPS[properties]
        RBE[rentsecure_be]
    end

    NS_WA --> PROPS
    NS_WA --> RBE
    NS_VN --> PROPS
    NS_VN --> NS_VOICE
    NS_VN --> NS_WA
    NS_RENT --> NS_VOICE
    NS_RENT --> NS_WA
    NS_RENT --> RBE
    NS_EC --> PROPS
    NS_EC --> NS_VOICE
    NS_EC --> NS_WA
    NS_EC --> RBE
    NS_SCHED --> PROPS
    NS_SCHED --> NS_VOICE
    NS_SCHED --> NS_WA
    NS_LATE --> NS_WA
    NS_COMM --> NS_NOTIF
    NS_COMM --> NS_SMS
    NS_COMM --> NS_WA
```

## Finance Dependency Graph

```mermaid
graph TD
    subgraph "finance"
        FM[finance.models]
        FV[finance.views]
        FSER[finance.serializers]
        FUTIL[finance.utils]
    end

    subgraph "External"
        CORE[core]
        PROPS[properties]
        RBE[rentsecure_be]
    end

    FM --> RBE
    FV --> CORE
    FV --> PROPS
    FV --> RBE
    FUTIL --> PROPS
```

## Evidence Notes

- All diagrams are derived from `docs/architecture/audit_data.json` (AST-based analysis).
- Cross-app import count: 205
- Total modules analyzed: 321
- Total imports: 387
- Source: `scripts/arch_audit.py` (AST-based static analysis)
