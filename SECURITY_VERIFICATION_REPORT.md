# SECURITY VERIFICATION REPORT

**Project:** RentSecureBE
**Audit Date:** 2026-06-23
**Verification Type:** Deep code-level verification of 4 webhook/function-based view endpoints
**Auditor:** Senior Application Security Engineer
**Methodology:** Static code analysis, URL routing verification, import tracing, authentication/authorization flow analysis

---

## Executive Summary

| # | Endpoint | File | Audit Finding | Verification Result | Severity |
|---|----------|------|---------------|---------------------|----------|
| 1 | `cashfree_payout_webhook` | `core/views.py:323` | No signature validation, no auth, no CSRF | **VALID** | Critical |
| 2 | `leegality_webhook` | `properties/views/unit_views.py:304` | No signature validation, no auth, no CSRF | **VALID** | Critical |
| 3 | `whatsapp_webhook` | `ai_assistant/views.py:216` | No signature validation, no auth, no CSRF | **PARTIALLY VALID** (latent — currently unreachable) | High |
| 4 | `retry_signature` | `dashboard/views.py:14` | No authentication, no CSRF, no ownership | **VALID** | Critical |

---

## 1. cashfree_payout_webhook

### 1.1 Complete Source Code

**File:** `core/views.py`
**Lines:** 323-354

```python
@csrf_exempt
def cashfree_payout_webhook(request: HttpRequest) -> JsonResponse:
    """Handle Cashfree payout status webhook.

    Fixed: rent.save() no longer overwrites `rent` with None.
    Fixed: Removed invalid rent.renter.property.owner chain.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    payload = json.loads(request.body)
    transfer_id = payload.get("transferId")
    event_status = payload.get("event")

    try:
        rent = RentRecord.objects.get(payout_reference=transfer_id)
    except RentRecord.DoesNotExist:
        return JsonResponse({"error": "Invalid transfer ID"}, status=404)

    if event_status == "TRANSFER_SUCCESS":
        rent.payout_status = "SUCCESS"
    elif event_status == "TRANSFER_FAILED":
        rent.payout_status = "FAILED"
    rent.save()

    # Send payout notification
    try:
        send_payout_notification(rent)
    except Exception as e:
        logger.warning(f"Failed to send payout notification for rent {rent.id}: {e}")

    return JsonResponse({"message": "Webhook received"}, status=200)
```

### 1.2 URL Routing Verification

**File:** `core/urls.py`
**Lines:** 36-39

```python
path(
    "webhook/cashfree/payout/",
    cashfree_payout_webhook,
    name="cashfree_payout_webhook",
),
```

**Included in:** `rentsecure_be/urls.py:25` → `path("api/", include("core.urls"))`

**Full exposed URL:** `POST /api/webhook/cashfree/payout/`

**Status:** ACTIVE and REACHABLE.

### 1.3 Security Controls Assessment

| Control | Present? | Evidence |
|---------|----------|----------|
| CSRF protection | NO | `@csrf_exempt` at line 323 |
| Authentication | NO | No `@permission_classes`, no `request.user` check, no token validation |
| Signature validation | NO | No HMAC, no header inspection, no shared secret check |
| Ownership check | NO | `RentRecord.objects.get(payout_reference=transfer_id)` — no owner verification |
| Estado guard | NO | Blindly overwrites `payout_status` to SUCCESS or FAILED regardless of current state |
| Idempotency | NO | Every call triggers `send_payout_notification(rent)` regardless of current state |
| Structured logging | NO | Only `logger.warning` on exception (line 352); no info/audit logs for accepted/rejected webhooks |
| Rate limiting | NO | None |

### 1.4 Audit Finding Confirmation

**Result: VALID**

The audit finding is fully confirmed. The endpoint accepts unauthenticated, unsigned POST requests and modifies critical financial state (`RentRecord.payout_status`) without any verification.

### 1.5 Exploit Path

**Attacker capability:** Any internet host that can send HTTP POST requests.

**Steps:**
1. Attacker discovers or guesses a `transferId`. The code at `rentsecure_be/services/cashfree_service.py:62` constructs `transfer_id = f"rent_{rent.id}"` where `rent.id` is an auto-incrementing integer. This makes `transferId` sequentially guessable (`rent_1`, `rent_2`, etc.).
2. Attacker sends:
   ```http
   POST /api/webhook/cashfree/payout/
   Content-Type: application/json

   {"transferId": "rent_123", "event": "TRANSFER_SUCCESS"}
   ```
3. The endpoint sets `rent.payout_status = "SUCCESS"` and calls `send_payout_notification(rent)`, sending a fake "payout successful" WhatsApp to the tenant.
4. Attacker can also forge `TRANSFER_FAILED` to:
   - Prevent legitimate payouts from being recognized
   - Trigger `core/views.py:560` bulk status reset (when owner updates bank details)
   - Cause `properties/communication/retry_failed_payouts.py` retry storms

**Impact:**
- **Financial:** Owner accounting reports become false; tax filings corrupted; real payout failures hidden
- **Tenant:** Fake payout confirmation messages sent to tenants; confusion about actual payment status
- **Downstream:** `pay_owner_after_rent` in `cashfree_service.py:47` early-returns if `payout_status == "SUCCESS"`, so forged SUCCESS prevents real Cashfree transfer from being retried

### 1.6 Production-Grade Fix Plan

**Requirements:**
1. Implement HMAC-SHA256 signature validation per Cashfree official documentation
2. Read `x-webhook-signature` and `x-webhook-timestamp` headers
3. Validate `HMAC-SHA256(secret, timestamp + raw_body)` against header
4. Add estado guard: block `SUCCESS → FAILED` transition; allow `PENDING→SUCCESS`, `PENDING→FAILED`, `FAILED→SUCCESS`
5. Add idempotency: if `payout_status` already matches incoming event, skip save and skip notification
6. Add structured logging for every webhook attempt
7. Empty `CASHFREE_WEBHOOK_SECRET` → skip validation (safe rollout)

**Implementation effort:** Medium
**Breaking-change risk:** Low (safe rollout with empty secret)

---

## 2. leegality_webhook

### 2.1 Complete Source Code

**File:** `properties/views/unit_views.py`
**Lines:** 304-342

```python
@csrf_exempt
def leegality_webhook(request: HttpRequest) -> JsonResponse:
    """Process Leegality signing-status callbacks.

    Updates ``owner_signed`` / ``renter_signed`` flags based on the
    document state. The endpoint is intentionally permissive — it
    always returns ``200`` so Leegality does not retry indefinitely.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload: dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid payload"}, status=400)

    doc_id: str | None = (
        payload.get("document_id")
        or payload.get("documentId")
        or payload.get("documentKey")
    )
    status_value: str | None = payload.get("status") or payload.get("state")
    participant: str | None = payload.get("participant") or payload.get("identifier")

    agreement: RentAgreementDraft | None = RentAgreementDraft.objects.filter(
        leegality_document_id=doc_id
    ).first()
    if agreement is not None and status_value is not None:
        if status_value.upper() == "SIGNED":
            if participant and participant.upper() == "OWNER":
                agreement.owner_signed = True
            elif participant and participant.upper() == "RENTER":
                agreement.renter_signed = True
            else:
                agreement.owner_signed = True
                agreement.renter_signed = True
            agreement.save(update_fields=["owner_signed", "renter_signed"])

    return JsonResponse({"status": "ok"})
```

### 2.2 URL Routing Verification

**File:** `properties/urls.py`
**Line:** 56

```python
path("leegality/webhook/", leegality_webhook),
```

**Included in:** `rentsecure_be/urls.py:28` → `path("properties/", include("properties.urls"))`

**Full exposed URL:** `POST /properties/leegality/webhook/`

**Status:** ACTIVE and REACHABLE.

### 2.3 Security Controls Assessment

| Control | Present? | Evidence |
|---------|----------|----------|
| CSRF protection | NO | `@csrf_exempt` at line 304 |
| Authentication | NO | No `@permission_classes`, no `request.user` check |
| Signature validation | NO | No `mac` field validation, no HMAC-SHA1 check against `privateSalt` |
| Ownership check | NO | Looks up `RentAgreementDraft` by `leegality_document_id` only; no user/owner verification |
| Payload integrity | NO | No HMAC, no checksum, no signature of any kind |
| Structured logging | NO | No logging at all in this function |
| Replay protection | NO | No timestamp, nonce, or idempotency key check |

**Additional observation:** The docstring explicitly states: *"The endpoint is intentionally permissive — it always returns 200 so Leegality does not retry indefinitely."* This confirms the permissiveness is a deliberate design choice, not an oversight.

### 2.4 Audit Finding Confirmation

**Result: VALID**

The audit finding is fully confirmed. The endpoint accepts unauthenticated, unsigned POST requests and modifies legally sensitive state (`RentAgreementDraft.owner_signed`, `renter_signed`) without any verification.

### 2.5 Exploit Path

**Attacker capability:** Any internet host that can send HTTP POST requests.

**Steps:**
1. Attacker needs a `document_id` (stored in `RentAgreementDraft.leegality_document_id`). IDs may be guessable or discoverable via:
   - Leegality dashboard enumeration
   - API responses when owner creates agreements
   - Sequential IDs if Leegality returns predictable document IDs
2. Attacker sends:
   ```http
   POST /properties/leegality/webhook/
   Content-Type: application/json

   {"document_id": "doc_abc", "status": "SIGNED", "participant": "OWNER"}
   ```
3. The endpoint sets `agreement.owner_signed = True` and `agreement.renter_signed = True` (line 333-339).
4. The `RentAgreementDraft` is now marked as fully signed without any actual e-signature from the tenant.

**Impact:**
- **Legal:** Agreement marked as signed without tenant consent; document may not satisfy Indian IT Act e-signature requirements
- **Tenant:** False legal consent recorded; tenant may be bound by terms they never agreed to
- **Owner:** No valid audit trail from Leegality; if challenged, owner cannot produce proof of tenant signature
- **Downstream:** Any logic checking `owner_signed` and `renter_signed` (agreement completion, PDF finalization, tenant onboarding) will treat the forged agreement as valid

### 2.6 Production-Grade Fix Plan

**Requirements:**
1. Implement HMAC-SHA1 signature validation per Leegality official documentation
2. Verify `mac` field in payload against `HMAC-SHA1(documentId, privateSalt)`
3. Add `LEEGALITY_PRIVATE_SALT` setting (new environment variable)
4. Add structured logging for every webhook attempt
5. Empty `LEEGALITY_PRIVATE_SALT` → skip validation (safe rollout)

**Implementation effort:** Medium
**Breaking-change risk:** Low (safe rollout with empty salt)

---

## 3. whatsapp_webhook

### 3.1 Complete Source Code

**File:** `ai_assistant/views.py`
**Lines:** 216-230

```python
@csrf_exempt
def whatsapp_webhook(request: HttpRequest) -> JsonResponse:
    payload = json.loads(request.body)
    phone = payload.get("from")
    message = payload.get("text")

    # user = get_user_by_whatsapp_number(phone)
    try:
        user = UserProfile.objects.get(whatsapp_number=phone)
    except UserProfile.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)

    reply = handle_chat_message(user, message)
    send_whatsapp_message(phone, reply)
    return JsonResponse({"message": "OK"})
```

### 3.2 URL Routing Verification

**File:** `ai_assistant/urls.py`
**Line:** 7

```python
urlpatterns = [path("webhooks/whatsapp/", whatsapp_webhook, name="whatsapp_webhook")]
```

**Included in:** `rentsecure_be/urls.py`

**VERIFICATION RESULT:** `ai_assistant/urls.py` is **NOT included** in `rentsecure_be/urls.py`. The root URL configuration includes:
- `core.urls`
- `properties.urls` (twice)
- `finance.urls`
- `documents.urls`
- `dashboard.urls`

There is **NO** `path("ai_assistant/", include("ai_assistant.urls"))` or similar entry.

**Additionally:** `ai_assistant` is **NOT** in `INSTALLED_APPS` (`rentsecure_be/settings.py:103-123`).

**Status:** The endpoint exists in code but is **CURRENTLY UNREACHABLE** through normal URL routing.

### 3.3 Security Controls Assessment

| Control | Present? | Evidence |
|---------|----------|----------|
| CSRF protection | NO | `@csrf_exempt` at line 216 |
| Authentication | NO | No `@permission_classes`, no `request.user` check |
| Signature validation | NO | No Twilio/Meta webhook signature validation |
| Rate limiting | NO | None |
| Input validation | NO | Direct `payload.get("from")` and `payload.get("text")` without sanitization |
| User enumeration | YES (vulnerability) | Different response for `UserProfile.DoesNotExist` (404) vs found (200 + message sent) |

### 3.4 Audit Finding Confirmation

**Result: PARTIALLY VALID**

The code is vulnerable, but the endpoint is **currently unreachable** because:
1. `ai_assistant/urls.py` is not included in the root URL configuration
2. `ai_assistant` is not in `INSTALLED_APPS`

**However:** The code is a **latent vulnerability**. If someone adds `ai_assistant/urls.py` to the root URLconf in the future (e.g., `path("ai_assistant/", include("ai_assistant.urls"))`), the endpoint would immediately become exploitable without any additional changes.

### 3.5 Exploit Path (If Endpoint Were Activated)

**Attacker capability:** Any internet host (if URL is ever wired up).

**Steps:**
1. Attacker sends:
   ```http
   POST /ai_assistant/webhooks/whatsapp/
   Content-Type: application/json

   {"from": "+919999999999", "text": "malicious payload"}
   ```
2. Endpoint looks up `UserProfile` by WhatsApp number (line 224)
3. If found, calls `handle_chat_message(user, message)` — triggers AI processing
4. Sends WhatsApp reply to the user via `send_whatsapp_message(phone, reply)` (line 229)
5. Attacker can:
   - Enumerate users by trying phone numbers (404 vs 200 response difference)
   - Trigger AI-generated messages to any user
   - Potentially extract AI responses (information disclosure)
   - Cause DoS by flooding with requests

**Impact:**
- **User enumeration:** Different HTTP status codes reveal whether a WhatsApp number is registered
- **Abuse of AI service:** Attacker can force the system to process arbitrary inputs and send WhatsApp messages
- **Cost:** Each triggered WhatsApp message may incur API costs
- **Reputation:** Fake AI-generated messages sent to real users

### 3.6 Production-Grade Fix Plan

**Requirements:**
1. Add Twilio/Meta webhook signature validation (whichever WhatsApp provider is used)
2. Add rate limiting per phone number
3. Uniform error response (do not reveal whether user exists)
4. If the endpoint is needed, wire it up properly with `ai_assistant` in `INSTALLED_APPS` and URLconf

**Implementation effort:** Small (if kept) or None (if deleted)
**Breaking-change risk:** None (currently unreachable)

**Recommendation:** Either remove the dead endpoint entirely, or implement it properly with provider signature validation before wiring it into URLs.

---

## 4. retry_signature

### 4.1 Complete Source Code

**File:** `dashboard/views.py`
**Lines:** 1-20 (entire file)

```python
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from properties.models import RentRecord
from smartbot.actions import send_agreement_for_signature


def agreement_status_view(request: HttpRequest) -> HttpResponse:
    records = RentRecord.objects.select_related("renter").all().order_by("-created_at")
    return render(request, "dashboard/agreement_status.html", {"records": records})


@csrf_exempt
def retry_signature(request: HttpRequest, rent_id: int) -> HttpResponse:
    if request.method == "POST":
        rent = RentRecord.objects.get(id=rent_id)
        if rent.renter is not None:
            send_agreement_for_signature(rent.renter.name)
    return redirect("agreement_status")
```

### 4.2 URL Routing Verification

**File:** `dashboard/urls.py`
**Lines:** 9-11

```python
path("agreements/", views.agreement_status_view, name="agreement_status"),
path(
    "retry-signature/<int:rent_id>/", views.retry_signature, name="retry_signature"
),
```

**Included in:** `rentsecure_be/urls.py:31` → `path("dashboard/", include("dashboard.urls"))`

**Full exposed URL:** `POST /dashboard/retry-signature/<rent_id>/`

**Status:** ACTIVE and REACHABLE.

### 4.3 Security Controls Assessment

| Control | Present? | Evidence |
|---------|----------|----------|
| CSRF protection | NO | `@csrf_exempt` at line 14 |
| Authentication | NO | No `@permission_classes`, no `request.user` check |
| Authorization/Ownership | NO | `RentRecord.objects.get(id=rent_id)` — no check that `request.user` owns the unit |
| Method restriction | PARTIAL | Checks `request.method == "POST"` but `@csrf_exempt` means any method works in practice |
| Input validation | NO | `rent_id` passed directly to `.get(id=rent_id)` without sanitization |
| Logging | NO | No logging of who triggered retry or for which rent |

**Additional observations:**
- No `try/except` around `RentRecord.objects.get()` — if `rent_id` doesn't exist, Django raises `Http404` which returns a 404 page. This is a minor information disclosure (confirms valid/invalid IDs).
- `send_agreement_for_signature(rent.renter.name)` — only passes `name`, not the full `Renter` object or agreement context. This may fail silently if the function expects more arguments.
- The function always redirects to `agreement_status` regardless of success/failure — no feedback to caller.

### 4.4 Audit Finding Confirmation

**Result: VALID**

The audit finding is fully confirmed. The endpoint has:
1. No authentication — any unauthenticated user can access it
2. No authorization/ownership check — any user can trigger signature retry for any rent record, even ones they don't own
3. No CSRF protection

### 4.5 Exploit Path

**Attacker capability:** Any unauthenticated internet user.

**Steps:**
1. Attacker enumerates rent IDs (sequential integers starting from 1).
2. Attacker sends:
   ```http
   POST /dashboard/retry-signature/42/
   ```
3. For rent ID 42:
   - If `rent.renter` exists, `send_agreement_for_signature(rent.renter.name)` is called
   - This triggers a new Leegality signature request to the renter
4. Attacker can iterate through all rent IDs, causing:
   - Mass spam of signature requests to all renters
   - Confusion and potential phishing-like behavior (renters receive unexpected "please sign" emails)
   - Denial of service against Leegality API (rate limit exhaustion)
   - Potential Leegality account suspension for abuse

**Impact:**
- **Tenant harassment:** Mass unsolicited signature requests
- **Leegality abuse:** API rate limits exhausted; potential account suspension
- **Owner confusion:** Owners receive unexpected signature requests for their own agreements
- **Reputation:** Tenants lose trust in the platform due to unexpected emails

### 4.6 Production-Grade Fix Plan

**Requirements:**
1. Add `@permission_classes([IsAuthenticated])` — require authenticated session
2. Add ownership check: `rent.renter.unit.owner == request.user`
3. Remove `@csrf_exempt` — DRF handles CSRF for authenticated sessions
4. Add structured logging: who triggered retry, which rent, timestamp
5. Add rate limiting per user (e.g., max 5 retries per hour per rent record)
6. Add `try/except` for `RentRecord.DoesNotExist` to return 404 cleanly
7. Consider whether this endpoint should exist at all — `send_agreement_for_signature` should ideally be triggered explicitly by the owner from a dedicated UI, not via a public POST endpoint

**Implementation effort:** Small
**Breaking-change risk:** Low — authenticated owner-only access is the correct behavior. Any legitimate usage (owner retrying their own agreement) will continue to work.

---

## 5. SUMMARY TABLE

| # | Endpoint | Reachable? | Auth | CSRF | Signature | Ownership | Verdict | Severity |
|---|----------|-----------|------|------|-----------|-----------|---------|----------|
| 1 | cashfree_payout_webhook | YES | None | Exempt | None | None | VALID | Critical |
| 2 | leegality_webhook | YES | None | Exempt | None | None | VALID | Critical |
| 3 | whatsapp_webhook | NO (latent) | None | Exempt | None | None | PARTIALLY VALID | High |
| 4 | retry_signature | YES | None | Exempt | N/A | None | VALID | Critical |

---

## 6. RECOMMENDED FIX PRIORITY

| Priority | Endpoint | Rationale |
|----------|----------|-----------|
| **P1** | `cashfree_payout_webhook` | Direct financial impact; actively exploitable; unauthenticated |
| **P1** | `leegality_webhook` | Legal/compliance impact; actively exploitable; unauthenticated |
| **P2** | `retry_signature` | Abuse/DoS impact; actively exploitable; unauthenticated |
| **P3** | `whatsapp_webhook` | Latent (unreachable); fix before wiring into URLs or delete dead code |

---

## 7. COMMON ROOT CAUSE

All 4 endpoints share the same architectural flaw: **function-based views handling external callbacks without Django REST Framework permission classes or provider-specific signature validation.**

The Razorpay webhook (`core/views.py:415`) is the exception — it uses `@csrf_exempt` but implements HMAC signature validation via `check_signature_or_return_http_response`. This pattern should be applied to all webhook endpoints.

---

*End of Security Verification Report*
