# RAG-015 — External Integrations

**Metadata:** `id=RAG-015` | `tags=twilio,razorpay,cashfree,leegality,openai,aws`

## Environment variables (see RAG-020)

| Service | Settings keys |
|---------|----------------|
| Twilio | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `TWILIO_WHATSAPP_NUMBER` |
| Razorpay | `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` |
| Cashfree | `CASHFREE_CLIENT_ID`, `CASHFREE_CLIENT_SECRET`, payout base URLs |
| Leegality | `LEEGALITY_API_KEY`, `LEEGALITY_ORG_ID`, `LEEGALITY_WORKFLOW_ID`, `LEEGALITY_TEMPLATE_ID` |
| OpenAI | `OPENAI_API_KEY` |
| FCM | `FCM_SERVER_KEY` |
| AWS S3 | `AWS_S3_BUCKET_NAME`, `AWS_S3_REGION_NAME` |
| Email | `EMAIL_HOST`, `EMAIL_HOST_USER`, etc. |

## Twilio

- OTP SMS in production (`DEBUG=False`)
- WhatsApp messages for rent links, reminders, alerts

## Razorpay

- Payment links for rent collection
- Webhook: `/api/rent/payment-callback/`

## Cashfree

- Beneficiary registration for owners
- Payout API via `rentsecure_be/utils/cashfree_payout.py`
- Webhook: `/api/webhook/cashfree/payout/`

## Leegality

- E-sign rent agreements from `RentAgreementDraftViewSet`
- Service: `rentsecure_be/services/leegality_service.py`
- Webhook: `/api/leegality/webhook/`

## OpenAI

- SmartBot: `smartbot/services/gpt_services.py`

## Storage

- Media: `MEDIA_ROOT` local; S3 optional for production uploads

## Frontend

- `FRONTEND_URL`, `BACKEND_URL` in settings for links in messages
