# RentSecureBE Production Architecture

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | Approved |
| **Date** | 2026-07-14 |
| **Author** | RentSecure Engineering |
| **Scope** | Production infrastructure, platform services, and phased evolution strategy for RentSecureBE |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Constraints & Budget](#2-business-constraints--budget)
3. [Payment Strategy](#3-payment-strategy)
4. [Notification Strategy](#4-notification-strategy)
5. [Background Jobs Strategy](#5-background-jobs-strategy)
6. [Cache Strategy](#6-cache-strategy)
7. [Search Strategy](#7-search-strategy)
8. [File Storage Strategy](#8-file-storage-strategy)
9. [Observability Strategy](#9-observability-strategy)
10. [Deployment Strategy](#10-deployment-strategy)
11. [Infrastructure Cost Breakdown](#11-infrastructure-cost-breakdown)
12. [Application Architecture Requirements](#12-application-architecture-requirements)
13. [Upgrade Path Summary](#13-upgrade-path-summary)

---

## 1. Executive Summary

RentSecureBE is a Django + DRF modular monolith built with Clean Architecture, Domain-Driven Design, and enterprise-grade code quality. The production architecture is designed to operate within a strict monthly budget of ₹2,000–3,000 INR (~$24–36 USD) for Year 1, while maintaining full upgradeability to 1 Million users without changing business logic.

**Year 1 Philosophy:**
- Use AWS Free Tier wherever possible
- Prefer operational simplicity over distributed complexity
- Use only services that are actually needed
- Keep premium integrations behind feature flags with interfaces, adapters, and dependency injection already implemented
- Avoid Kubernetes, EKS, ECS, Service Mesh, Kafka, RabbitMQ, OpenSearch

**Key Principle:** The codebase contains interfaces and adapters for future premium services, but they remain disabled in Year 1. UI displays "Coming Soon" until explicitly enabled.

---

## 2. Business Constraints & Budget

### 2.1 Year 1 Financial Constraints

- **Monthly Infrastructure Budget:** ₹2,000–3,000 INR ($24–36 USD)
- **Goal:** Run for at least the first year within budget
- **Architecture Philosophy:** Cost-efficient, upgradeable, no major rewrites

### 2.2 AWS Free Tier Usage (Months 1–12)

| Service | Free Tier Benefit | Year 1 Status |
|---------|-------------------|---------------|
| EC2 | 750 hours/month of t2.micro or t3.micro | Used for initial instance |
| RDS | 750 hours/month of db.t2.micro or db.t3.micro | Used for initial database |
| S3 | 5 GB standard storage | Primary file storage |
| CloudWatch | 10 custom metrics, 10 alarms, 1 GB logs | Basic observability |
| Data Transfer | 15 GB out | Sufficient for MVP |

### 2.3 Post-Free-Tier Budget (After 12 Months)

| Resource | Recommended | Est. Monthly Cost (USD) | Est. Monthly Cost (INR) |
|----------|-------------|------------------------|------------------------|
| EC2 | t3.small | ~$15 | ~₹1,250 |
| RDS | db.t3.small | ~$15 | ~₹1,250 |
| S3 | Standard | ~$0.50 | ~₹40 |
| CloudWatch | Basic | ~$3 | ~₹250 |
| **Total** | | **~$33.50** | **~₹2,790** |

**Note:** Start with t3.micro/t3.micro and upgrade to t3.small when utilization consistently exceeds 70%.

---

## 3. Payment Strategy

### 3.1 Year 1 Architecture

**Current Solution:** Completely free, manual UPI-based payment flow.

#### Flow Design

```
Owner Registration
├── UPI ID
├── QR Code (image upload)
└── Bank Account Details

Tenant Payment Flow
├── Tenant clicks "Pay Rent"
├── Application displays owner's payment details
├── Tenant pays via any UPI app (GPay, PhonePe, Paytm, etc.)
├── Tenant submits:
│   ├── UTR (required)
│   ├── Screenshot (optional)
│   └── Payment note (optional)
├── Status: Payment Submitted
├── Owner reviews payment
├── Owner clicks: Approve / Reject
├── If Approved:
│   ├── Rent Receipt PDF generated (WeasyPrint)
│   ├── Receipt emailed to tenant
│   └── Status: Paid
└── If Rejected:
    ├── Tenant notified with reason
    └── Status: Rejected
```

#### Implementation Requirements

- **Payment Service Interface:** `payments.ports.PaymentGateway`
- **Adapters:** `payments.adapters.manual.ManualPaymentAdapter`
- **Feature Flags:**
  - `PAYMENT_GATEWAY_ENABLED` = `False`
  - `UPI_PAYMENT_ENABLED` = `True`
- **Domain Events:**
  - `PaymentSubmitted`
  - `PaymentVerified`
  - `PaymentRejected`
  - `ReceiptGenerated`
- **UI:** "Coming Soon" badge on Cashfree/Razorpay options

#### Why This Works for Year 1

- Zero transaction fees
- No payment gateway integration complexity
- No PCI compliance burden
- No webhook handling
- No settlement delays
- Owner maintains full control over funds

---

### 3.2 Stage 2

**Trigger Point:** Monthly transaction volume exceeds 500 payments/month OR manual verification overhead exceeds 10 hours/week.

**Upgrade:**
- Enable `PAYMENT_GATEWAY_ENABLED` feature flag
- Integrate Razorpay or Cashfree
- Auto-capture payments via payment links
- Webhook-based verification replaces manual approval
- Keep manual UPI as fallback for owners who prefer it

**Migration Strategy:**
1. Implement `payments.adapters.razorpay.RazorpayAdapter` and `payments.adapters.cashfree.CashfreeAdapter`
2. Both adapters implement `PaymentGateway` interface
3. Switch via environment variable or feature flag
4. Run dual-mode for 30 days (both manual and gateway)
5. Migrate owners gradually based on preference
6. Decommission manual adapter after 90 days of stable gateway operation

**Code Impact:**
- No business logic changes required
- Only adapter implementation and configuration change
- Domain events remain identical

---

### 3.3 Stage 3

**Upgrade:**
- Smart payment routing based on owner preference, amount, or tenant location
- Subscription/recurring payment support
- Partial payments and installments
- Payment reminders and auto-retries
- Advanced reconciliation and reporting

---

### 3.4 Stage 4

**Upgrade:**
- Global payment orchestration
- Multi-currency support
- Advanced fraud detection
- Dynamic pricing and late fees
- Split payments (owner + platform fee)

---

## 4. Notification Strategy

### 4.1 Year 1 Architecture

**Current Solution:** Free notification channels only.

#### Channels Enabled

| Channel | Provider | Cost | Use Case |
|---------|----------|------|----------|
| Email | Django SMTP / AWS SES Free Tier | Free (first 62,000 emails/month) | Receipts, alerts, password reset |
| Push Notifications | Firebase Cloud Messaging (FCM) | Free | Real-time alerts, payment reminders |
| In-App Notifications | Database-backed (PostgreSQL) | Free | Activity feed, announcements |

#### Channels Disabled (Feature Flags)

| Channel | Status | Future Upgrade |
|---------|--------|---------------|
| WhatsApp Business API | `False` | Stage 2 |
| SMS (Twilio / MSG91 / etc.) | `False` | Stage 2 |
| Voice Calls | `False` | Stage 3 |
| Telegram Bot | `False` | Stage 3 |

#### Implementation Requirements

- **Notification Service Interface:** `notifications.ports.NotificationChannel`
- **Adapters:**
  - `notifications.adapters.email.EmailAdapter`
  - `notifications.adapters.fcm.FirebaseAdapter`
  - `notifications.adapters.inapp.InAppAdapter`
  - `notifications.adapters.whatsapp.WhatsAppAdapter` (disabled)
  - `notifications.adapters.sms.SMSAdapter` (disabled)
- **Feature Flags:**
  - `WHATSAPP_NOTIFICATIONS_ENABLED` = `False`
  - `SMS_NOTIFICATIONS_ENABLED` = `False`
- **UI:** "Coming Soon" badge on WhatsApp/SMS notification preferences

---

### 4.2 Stage 2

**Trigger Point:** User feedback indicates demand for WhatsApp/SMS OR email open rates drop below 20%.

**Upgrade:**
- Enable WhatsApp Business API via Twilio or Interakt
- Enable SMS via MSG91 or Twilio
- Template management for WhatsApp/SMS
- Fallback logic: WhatsApp → SMS → Email → Push

**Migration Strategy:**
1. Implement adapters with full provider abstraction
2. Test in sandbox environment
3. Enable for 10% of users (canary)
4. Monitor delivery rates and costs
5. Full rollout after 2 weeks of stable operation

---

### 4.3 Stage 3

**Upgrade:**
- Advanced preference center
- Notification batching and digests
- Time-zone-aware delivery
- A/B testing for notification content
- Voice call integration for critical alerts

---

### 4.4 Stage 4

**Upgrade:**
- AI-powered notification timing
- Personalization engine
- Multi-language support
- Advanced analytics and attribution

---

## 5. Background Jobs Strategy

### 5.1 Year 1 Architecture

**Current Solution:** Django management commands + cron/systemd timers. No Celery.

#### Rationale

- Single EC2 instance means no distributed worker need
- No message broker required
- Zero additional infrastructure cost
- Simpler debugging and monitoring
- Sufficient for < 10K users

#### Implementation

| Job Type | Solution | Example |
|----------|----------|---------|
| Daily reminders | systemd timer + management command | `send_rent_reminders` |
| Weekly reports | cron + management command | `generate_weekly_reports` |
| Receipt generation | Synchronous in request (fast) or async in same process | `generate_receipt` |
| Cleanup tasks | systemd timer | `cleanup_old_sessions` |
| Payment verification polling | cron + query | `check_pending_payments` |

#### Configuration

```python
# settings.py
BACKGROUND_JOBS_BACKEND = "cron"  # Options: "cron", "celery"

# crontab (managed via systemd timer or /etc/cron.d)
# Example: send rent reminders daily at 9 AM
0 9 * * * ubuntu /home/ubuntu/rentsecure/venv/bin/python manage.py send_rent_reminders >> /var/log/rentsecure/cron.log 2>&1
```

---

### 5.2 Stage 2

**Trigger Point:** Background tasks exceed 30 seconds execution time OR require retry/backoff logic OR user base exceeds 5,000.

**Upgrade:**
- Introduce Celery + Redis
- Move long-running tasks to async workers
- Implement task retries and exponential backoff
- Celery Beat replaces systemd timers

**Migration Strategy:**
1. Add `celery.py` to project
2. Configure Redis as broker (can use same Redis instance as cache)
3. Move existing management commands to Celery tasks
4. Run both systems in parallel for 2 weeks
5. Decommission cron jobs after validation

---

### 5.3 Stage 3

**Upgrade:**
- Celery workers scaled horizontally
- Priority queues for critical tasks
- Task routing by domain (payments, notifications, documents)
- Dead letter queues for failed tasks

---

### 5.4 Stage 4

**Upgrade:**
- Event-driven architecture replaces batch jobs
- Event sourcing for audit trails
- Distributed task orchestration

---

## 6. Cache Strategy

### 6.1 Year 1 Architecture

**Current Solution:** Django Local Memory Cache + database-backed alternatives.

#### Configuration

```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
```

#### When to Use Cache

| Use Case | Solution | Rationale |
|----------|----------|-----------|
| Dashboard analytics | Database aggregation + cache timeout | Single instance, no concurrency issues |
| User permissions | In-memory per-process | Fast, no consistency issues across single process |
| API rate limiting | Database-backed counter | No Redis required |
| Feature flags | In-memory + DB persistence | Fast reads, durable source |
| Session storage | Database-backed sessions | No shared cache needed |

#### When Redis Becomes Necessary

- Multiple Gunicorn workers need shared cache
- Cache invalidation across processes becomes an issue
- Rate limiting needs atomic operations
- Session affinity becomes a problem with load balancer

**Migration Trigger:** When scaling beyond a single Gunicorn worker (> 4 workers) OR when cache hit rate drops below 60%.

---

### 6.2 Stage 2

**Upgrade:**
- Redis introduced as optional cache backend
- Session storage migrates to Redis
- Rate limiting uses Redis atomic counters
- Cache invalidation becomes consistent across workers

---

### 6.3 Stage 3

**Upgrade:**
- Redis Cluster for high availability
- Advanced caching patterns (cache-aside, write-through)
- Redis-backed Celery broker

---

### 6.4 Stage 4

**Upgrade:**
- Multi-tier caching (L1 in-memory, L2 Redis, L3 database)
- Distributed cache for multi-region deployment

---

## 7. Search Strategy

### 7.1 Year 1 Architecture

**Current Solution:** PostgreSQL full-text search.

#### Implementation

```python
# models.py
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

class Property(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()

    class Meta:
        indexes = [
            GinIndex(
                name="property_search_idx",
                fields=["name", "address"],
                opclasses=["gin_trgm_ops", "gin_trgm_ops"],
            )
        ]

# service.py
properties = Property.objects.annotate(
    rank=SearchRank(
        SearchVector("name", "address"),
        SearchQuery(query)
    )
).filter(search=query).order_by("-rank")
```

#### Capabilities

- Full-text search on property names, addresses, descriptions
- Trigram similarity for fuzzy matching
- Ranking and relevance scoring
- Filtering by location, price, amenities

---

### 7.2 Stage 2

**Upgrade:**
- PostgreSQL optimization
- Materialized views for analytics search
- Search result caching
- Autocomplete via PostgreSQL `pg_trgm`

---

### 7.3 Stage 3

**Trigger Point:** Search latency exceeds 500ms OR search feature complexity requires faceting, highlighting, or synonyms.

**Upgrade:**
- OpenSearch (or Elasticsearch) introduced
- Advanced search features:
  - Faceted search
  - Result highlighting
  - Synonym support
  - Typo tolerance
  - Geo-spatial search

**Migration Strategy:**
1. Create `search.ports.SearchEngine` interface
2. Implement `PostgresSearchAdapter` and `OpenSearchAdapter`
3. Dual-write to both systems during transition
4. Read from OpenSearch after indexing is complete
5. Decommission PostgreSQL search after validation

---

### 7.4 Stage 4

**Upgrade:**
- OpenSearch Cluster with multiple nodes
- AI-powered semantic search
- Personalized search results
- Multi-language search support

---

## 8. File Storage Strategy

### 8.1 Year 1 Architecture

**Current Solution:** Amazon S3 only. No CloudFront.

#### Implementation

```python
# settings.py
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

AWS_STORAGE_BUCKET_NAME = "rentsecure-production"
AWS_S3_REGION_NAME = "ap-south-1"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
```

#### Access Patterns

| File Type | Access Method | Rationale |
|-----------|---------------|-----------|
| Public files (property images) | Direct S3 URL | Low cost, simple |
| Private files (receipts, agreements) | Proxied through Django view | Security, access control |
| Uploads | Presigned URLs via Django view | Avoid exposing AWS credentials |

#### Why No CloudFront in Year 1

- Additional cost: ~$1–2/month for minimal usage
- Single region deployment (ap-south-1) has acceptable latency for India users
- Complexity not justified for < 10K users
- S3 direct access is fast enough for MVP

---

### 8.2 Stage 2

**Trigger Point:** Users report slow image loading OR bandwidth costs exceed 10 GB/month.

**Upgrade:**
- CloudFront CDN introduced
- S3 origin configured for CloudFront
- Signed URLs for private CloudFront distribution
- Cache invalidation for updated files

**Migration Strategy:**
1. Create CloudFront distribution pointing to S3
2. Update Django storage backend to use CloudFront domain
3. Update presigned URL generation for CloudFront
4. Gradual rollout with fallback to S3
5. Decommission direct S3 URLs after validation

---

### 8.3 Stage 3

**Upgrade:**
- Multi-region S3 replication
- Image optimization (resize, compress) via Lambda@Edge
- Advanced CDN caching rules

---

### 8.4 Stage 4

**Upgrade:**
- Global CDN with edge computing
- Video streaming support
- Advanced media processing pipeline

---

## 9. Observability Strategy

### 9.1 Year 1 Architecture

**Current Solution:** CloudWatch + Structured Logging + Health Endpoint.

#### Components

| Component | Tool | Configuration |
|-----------|------|---------------|
| Metrics | CloudWatch Basic | CPU, memory, disk, network |
| Logs | CloudWatch Logs | JSON structured logs |
| Alarms | CloudWatch Alarms | 5 basic alarms |
| Health | Django health endpoint | `/health/` |
| Tracing | None | Not required for single instance |

#### Structured Logging Format

```python
import json
import logging

logger = logging.getLogger("rentsecure")

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "user_id": getattr(record, "user_id", None),
            "request_id": getattr(record, "request_id", None),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)
```

#### CloudWatch Alarms

1. CPU utilization > 80% for 5 minutes
2. Memory utilization > 85% for 5 minutes
3. Disk usage > 80%
4. HTTP 5xx error rate > 5%
5. Health check failure

---

### 9.2 Stage 2

**Upgrade:**
- CloudWatch enhanced monitoring (1-minute intervals)
- AWS X-Ray for distributed tracing
- Custom application metrics (business KPIs)
- Log Insights queries for debugging

---

### 9.3 Stage 3

**Trigger Point:** Distributed tracing becomes necessary OR debugging production issues takes > 30 minutes.

**Upgrade:**
- OpenTelemetry collector
- Jaeger or Grafana for trace visualization
- Advanced dashboards for business metrics
- Anomaly detection

---

### 9.4 Stage 4

**Upgrade:**
- Full observability stack
- AI-powered anomaly detection
- Predictive alerting
- Service map and dependency tracking

---

## 10. Deployment Strategy

### 10.1 Year 1 Architecture

**Current Solution:** Single EC2 instance + RDS + S3 + GitHub Actions.

#### Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────┐
│                        AWS Cloud                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │                    VPC                            │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │         Public Subnet                       │  │  │
│  │  │  ┌─────────────┐     ┌──────────────────┐  │  │  │
│  │  │  │    EC2      │     │   Security Group │  │  │  │
│  │  │  │  (t3.micro) │     │  (Web Server)    │  │  │  │
│  │  │  │             │     │                  │  │  │  │
│  │  │  │  ┌───────┐  │     │  - Port 22 (SSH)│  │  │  │
│  │  │  │  │Nginx  │  │     │  - Port 80 (HTTP)│  │  │  │
│  │  │  │  └───────┘  │     │  - Port 443(HTTPS)│ │  │  │
│  │  │  │  ┌───────┐  │     └──────────────────┘  │  │  │
│  │  │  │  │Gunicorn│ │                            │  │  │
│  │  │  │  │(Django)│ │                            │  │  │
│  │  │  │  └───────┘  │                            │  │  │
│  │  │  └─────────────┘                            │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  │                                                  │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │         Private Subnet                      │ │  │
│  │  │  ┌──────────────────────────────────────┐  │ │  │
│  │  │  │     RDS PostgreSQL                   │  │ │  │
│  │  │  │     (db.t3.micro)                    │  │ │  │
│  │  │  │                                      │  │ │  │
│  │  │  │  - No public IP                     │  │ │  │
│  │  │  │  - Security group: EC2 only         │  │ │  │
│  │  │  │  - Automated backups (7 days)       │  │ │  │
│  │  │  └──────────────────────────────────────┘  │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│                                                       │
│  ┌───────────────────────────────────────────────────┐ │
│  │  S3 Bucket (rentsecure-production)                │ │
│  │  - Static files and media                         │ │
│  │  - Versioned uploads                              │ │
│  │  - Lifecycle policies for cost optimization       │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Stack Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| OS | Ubuntu 22.04 LTS | EC2 AMI |
| Web Server | Nginx | Reverse proxy, static files, SSL termination |
| App Server | Gunicorn | WSGI server for Django |
| Application | Django 5.2 + DRF | Backend framework |
| Database | RDS PostgreSQL 15 | Primary data store |
| File Storage | S3 | Media and static files |
| CI/CD | GitHub Actions | Automated testing and deployment |
| SSL | ACM + Let's Encrypt | HTTPS certificates |
| DNS | Route53 (optional) | Custom domain |
| Process Manager | Systemd | Service management |

#### Deployment Pipeline

```yaml
# .github/workflows/deploy.yml (simplified)
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=.
      - run: ruff check .
      - run: mypy .
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to EC2
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /home/ubuntu/rentsecure
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python manage.py migrate
            python manage.py collectstatic --noinput
            sudo systemctl restart gunicorn
            sudo systemctl restart nginx
```

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name rentsecure.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name rentsecure.example.com;

    ssl_certificate /etc/letsencrypt/live/rentsecure.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rentsecure.example.com/privkey.pem;

    client_max_body_size 50M;

    location /static/ {
        alias /home/ubuntu/rentsecure/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/ubuntu/rentsecure/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Gunicorn Configuration

```bash
# /etc/systemd/system/gunicorn.service
[Unit]
Description=Gunicorn daemon for RentSecure
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/rentsecure
Environment="PATH=/home/ubuntu/rentsecure/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=rentsecure_be.settings.production"
ExecStart=/home/ubuntu/rentsecure/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    rentsecure_be.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### Security Groups

| Group | Inbound | Outbound |
|-------|---------|----------|
| EC2 Security Group | 22 (SSH, restricted IP), 80 (HTTP), 443 (HTTPS) | All |
| RDS Security Group | 5432 (PostgreSQL, EC2 SG only) | All |

---

### 10.2 Stage 2

**Trigger Point:** CPU utilization consistently > 70% OR memory usage > 80%.

**Upgrade:**
- Auto Scaling Group with 2+ EC2 instances
- Application Load Balancer (ALB)
- RDS Multi-AZ for high availability (optional)
- ElastiCache Redis for session storage and rate limiting
- CloudFront CDN for static assets

**Infrastructure Changes:**

```
┌──────────────────────────────────────────────────────────┐
│                      AWS Cloud                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │                    VPC                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │  EC2 (t3)   │  │  EC2 (t3)   │  │     ALB     │ │  │
│  │  │ Private AZ A│  │ Private AZ B│  │  (Public)   │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│  │         │                  │              │        │  │
│  │  ┌──────┴──────────────────┴──────────────┴───┐   │  │
│  │  │         RDS PostgreSQL (Multi-AZ)          │   │  │
│  │  │         db.t3.small (primary + standby)     │   │  │
│  │  └────────────────────────────────────────────┘   │  │
│  │  ┌────────────────────────────────────────────┐   │  │
│  │  │         ElastiCache Redis                  │   │  │
│  │  │         cache.t3.micro                     │   │  │
│  │  └────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  CloudFront + S3                                   │  │
│  │  - Static assets via CDN                           │  │
│  │  - Signed URLs for private files                   │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

### 10.3 Stage 3

**Upgrade:**
- Larger EC2 instances (t3.large or t3a.large)
- RDS read replicas for read-heavy workloads
- Enhanced monitoring (1-minute CloudWatch metrics)
- Advanced networking (VPC endpoints for S3)
- Database connection pooling (PgBouncer)

---

### 10.4 Stage 4

**Upgrade:**
- Container orchestration (EKS or ECS)
- Microservice extraction from modular monolith
- Full multi-AZ deployment
- Global CDN with edge computing
- Infrastructure as Code (Terraform/CloudFormation)

---

## 11. Infrastructure Cost Breakdown

### 11.1 Year 1 (Free Tier + Minimal)

| Service | Configuration | Free Tier? | Est. Monthly Cost (USD) | Est. Monthly Cost (INR) |
|---------|--------------|------------|------------------------|------------------------|
| EC2 | t3.micro (750 hrs) | Yes (12 months) | $0 | ₹0 |
| RDS | db.t3.micro (750 hrs) | Yes (12 months) | $0 | ₹0 |
| S3 | 5 GB standard | Yes | $0 | ₹0 |
| CloudWatch | Basic metrics | Yes | $0 | ₹0 |
| Data Transfer | 15 GB out | Yes | $0 | ₹0 |
| ACM | Public certificates | Yes | $0 | ₹0 |
| **Total** | | | **$0** | **₹0** |

**Actual Cost After Free Tier (Months 13+):**
| Service | Configuration | Est. Monthly Cost (USD) | Est. Monthly Cost (INR) |
|---------|--------------|------------------------|------------------------|
| EC2 | t3.small | $15.12 | ~₹1,250 |
| RDS | db.t3.small | $15.33 | ~₹1,280 |
| S3 | 10 GB + requests | $0.60 | ~₹50 |
| CloudWatch | Basic + 5 custom metrics | $3.00 | ~₹250 |
| Data Transfer | 20 GB out | $1.70 | ~₹140 |
| **Total** | | **~$35.75** | **~₹2,970** |

### 11.2 Stage 2

| Service | Configuration | Est. Monthly Cost (USD) | Est. Monthly Cost (INR) |
|---------|--------------|------------------------|------------------------|
| EC2 | 2x t3.small (ASG) | $30.24 | ~₹2,500 |
| ALB | Application Load Balancer | $22.00 | ~₹1,830 |
| RDS | db.t3.small Multi-AZ | $30.66 | ~₹2,550 |
| ElastiCache | cache.t3.micro | $11.00 | ~₹915 |
| S3 | 50 GB + requests | $1.20 | ~₹100 |
| CloudFront | 50 GB data transfer | $4.25 | ~₹355 |
| **Total** | | **~$99.35** | **~₹8,250** |

### 11.3 Stage 3

| Service | Configuration | Est. Monthly Cost (USD) | Est. Monthly Cost (INR) |
|---------|--------------|------------------------|------------------------|
| EC2 | 2x t3.large | $60.48 | ~₹5,020 |
| RDS | db.t3.large + 1 read replica | $91.98 | ~₹7,640 |
| ElastiCache | cache.t3.small cluster | $22.00 | ~₹1,830 |
| OpenSearch | t3.small search cluster | $45.00 | ~₹3,740 |
| CloudFront | 200 GB data transfer | $17.00 | ~₹1,410 |
| **Total** | | **~$236.46** | **~₹19,640** |

### 11.4 Stage 4

| Service | Configuration | Est. Monthly Cost (USD) | Est. Monthly Cost (INR) |
|---------|--------------|------------------------|------------------------|
| EKS | 3x t3.large nodes | $180.00 | ~₹14,950 |
| RDS | db.r5.large Multi-AZ + replicas | $200.00 | ~₹16,600 |
| ElastiCache | cache.r5.large cluster | $80.00 | ~₹6,650 |
| OpenSearch | r5.large search cluster | $150.00 | ~₹12,450 |
| CloudFront | 1 TB data transfer | $85.00 | ~₹7,060 |
| **Total** | | **~$695.00** | **~$57,710** |

**Note:** Stage 4 costs assume significant revenue to support the infrastructure.

---

## 12. Application Architecture Requirements

### 12.1 Non-Negotiable Patterns

These architectural patterns must be preserved through all stages:

| Pattern | Implementation | Rationale |
|---------|---------------|-----------|
| **Clean Architecture** | Domain layer has no framework imports | Testability, independence |
| **Domain-Driven Design** | Bounded contexts with explicit boundaries | Complexity management |
| **Modular Monolith** | Single deployable unit | Operational simplicity |
| **Repository Pattern** | `DomainRepository` interfaces | Persistence abstraction |
| **Unit of Work** | Transaction boundary management | Consistency |
| **Ports & Adapters** | Interface-driven dependencies | Testability, swapability |
| **CQRS Readiness** | Separate read/write models where needed | Performance |
| **Domain Events** | `DomainEvent` interface + handlers | Decoupling |
| **Feature Flags** | `features.flags.is_enabled()` | Safe rollouts |
| **Dependency Injection** | Constructor injection via `ServiceContainer` | Testability |
| **Strong Typing** | Full type hints, mypy strict | Reliability |
| **Testing Strategy** | Unit + Integration + Contract tests | Confidence |
| **Security** | RBAC, input validation, audit logs | Compliance |
| **Audit Logs** | `django-simple-history` | Traceability |
| **RBAC** | Role-based access control | Authorization |
| **Versioned APIs** | URL versioning (`/api/v1/`) | Backward compatibility |

### 12.2 Service Layer Architecture

```python
# Example: Payment Service
class PaymentService:
    def __init__(
        self,
        gateway: PaymentGateway,  # Injected via DI
        notifier: NotificationService,
        receipt_generator: DocumentService,
    ):
        self.gateway = gateway
        self.notifier = notifier
        self.receipt_generator = receipt_generator

    def submit_payment(self, tenant_id: int, amount: Decimal, utr: str) -> Payment:
        payment = self._create_payment_record(tenant_id, amount, utr)
        self._publish(PaymentSubmitted(payment.id))
        self.notifier.send(tenant_id, "Payment submitted for verification")
        return payment

    def approve_payment(self, payment_id: int, owner_id: int) -> Payment:
        payment = self._get_payment(payment_id)
        payment.mark_as_approved(owner_id)
        receipt = self.receipt_generator.generate(payment)
        self._publish(PaymentApproved(payment.id, receipt.id))
        self.notifier.send(payment.tenant_id, "Payment approved", receipt=receipt)
        return payment
```

### 12.3 Domain Events

```python
# Domain Events remain consistent across all stages
class DomainEvent:
    event_id: UUID
    occurred_at: datetime
    aggregate_id: UUID
    event_type: str

class PaymentSubmitted(DomainEvent):
    event_type = "payment.submitted"
    payment_id: UUID
    tenant_id: UUID
    amount: Decimal

class PaymentApproved(DomainEvent):
    event_type = "payment.approved"
    payment_id: UUID
    tenant_id: UUID
    receipt_id: UUID
```

### 12.4 Feature Flags

```python
# Feature flags control premium integrations
from features.flags import is_enabled

if is_enabled("CASHFREE_PAYMENTS_ENABLED"):
    gateway = CashfreeGateway()
else:
    gateway = ManualPaymentGateway()

if is_enabled("WHATSAPP_NOTIFICATIONS_ENABLED"):
    channel = WhatsAppChannel()
else:
    channel = EmailChannel()  # Fallback to free channel
```

---

## 13. Upgrade Path Summary

### 13.1 Decision Matrix

| Component | Year 1 | Stage 2 | Stage 3 | Stage 4 |
|-----------|--------|---------|---------|---------|
| **Payment** | Manual UPI | Razorpay/Cashfree | Smart routing | Global orchestration |
| **Notifications** | Email + FCM + In-App | WhatsApp + SMS | Voice + Telegram | AI-powered |
| **Background Jobs** | Cron + management commands | Celery + Redis | Priority queues | Event-driven |
| **Cache** | Django Local Memory | Redis | Redis Cluster | Multi-tier |
| **Search** | PostgreSQL full-text | PostgreSQL optimized | OpenSearch | OpenSearch Cluster |
| **File Storage** | S3 only | S3 + CloudFront | Multi-region S3 | Global CDN |
| **Observability** | CloudWatch Basic | CloudWatch + X-Ray | OpenTelemetry | Full observability |
| **Deployment** | Single EC2 | ASG + ALB + Redis | Read replicas | Container orchestration |

### 13.2 Upgrade Principles

1. **No Business Logic Changes:** All upgrades happen at the infrastructure and adapter layer only
2. **Feature Flags:** Every premium integration is behind a feature flag
3. **Interface Stability:** Domain interfaces never change; only implementations swap
4. **Gradual Migration:** Dual-run old and new systems during transition
5. **Rollback Ready:** Every stage change is reversible within 24 hours

### 13.3 Revenue-Based Triggers

| Trigger | Stage Upgrade |
|---------|---------------|
| 100 users | Stay on Year 1 |
| 1,000 users | Consider Stage 2 |
| 10,000 users | Stage 2 required |
| 100,000 users | Stage 3 required |
| 1,000,000 users | Stage 4 required |

### 13.4 Cost-Based Triggers

| Trigger | Action |
|---------|--------|
| Infrastructure cost > ₹3,000/month | Optimize Year 1 setup |
| Infrastructure cost > ₹8,000/month | Execute Stage 2 migration |
| Infrastructure cost > ₹20,000/month | Execute Stage 3 migration |
| Infrastructure cost > ₹60,000/month | Execute Stage 4 migration |

---

## Appendix A: Premium Service Migration Templates

### A.1 Payment Gateway Migration

```python
# Current (Year 1)
class ManualPaymentGateway(PaymentGateway):
    def create_payment(self, order: PaymentOrder) -> PaymentResult:
        return PaymentResult(status="manual", reference=order.id)

# Future (Stage 2)
class RazorpayGateway(PaymentGateway):
    def create_payment(self, order: PaymentOrder) -> PaymentResult:
        razorpay_order = razorpay_client.order.create({
            "amount": int(order.amount * 100),
            "currency": "INR",
            "receipt": order.id,
        })
        return PaymentResult(
            status="created",
            reference=razorpay_order["id"],
            payment_url=razorpay_order["short_url"],
        )
```

### A.2 Notification Channel Migration

```python
# Current (Year 1)
class EmailNotificationChannel(NotificationChannel):
    def send(self, recipient: str, message: str) -> NotificationResult:
        send_mail(subject, message, recipient)
        return NotificationResult(status="sent")

# Future (Stage 2)
class WhatsAppNotificationChannel(NotificationChannel):
    def send(self, recipient: str, message: str) -> NotificationResult:
        client.messages.create(
            from_="whatsapp:+14155238886",
            to=f"whatsapp:{recipient}",
            body=message,
        )
        return NotificationResult(status="sent")
```

---

*End of Production Architecture Document*
