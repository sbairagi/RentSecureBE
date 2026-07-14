# Finance and Payment Module Rules

Module-specific rules for finance, payments, and tax.

## Year 1 Payment Strategy

### Core Principle
Year 1 payment flow is completely free. Rent payment does NOT go through a payment gateway.

### Manual UPI Flow

**Owner Registration:**
- Owner registers UPI ID (e.g., `owner@upi`)
- Owner uploads QR Code image
- Owner provides Bank Account details (for reconciliation)

**Tenant Payment Flow:**
1. Tenant clicks "Pay Rent"
2. Application displays owner's payment details (UPI ID, QR, Bank Account)
3. Tenant pays directly using any UPI app (GPay, PhonePe, Paytm, etc.)
4. After payment, tenant uploads:
   - UTR (required)
   - Screenshot (optional)
   - Payment note (optional)
5. Status becomes `Payment Submitted`
6. Owner verifies manually
7. Owner clicks `Approve` or `Reject`
8. When approved:
   - Rent Receipt PDF is generated (WeasyPrint)
   - Receipt is emailed to tenant
   - Payment status becomes `Paid`

### Architecture Requirements

- **Payment Service Interface:** `payments.ports.PaymentGateway`
- **Year 1 Adapter:** `payments.adapters.manual.ManualPaymentAdapter`
- **Feature Flags:**
  - `CASHFREE_PAYMENTS_ENABLED` = `False`
  - `RAZORPAY_PAYMENTS_ENABLED` = `False`
  - `UPI_PAYMENT_ENABLED` = `True`
- **UI Requirement:** Display "Coming Soon" badge on Cashfree/Razorpay options

### Future Payment Gateway Integration (Stage 2)

The codebase MUST contain:
- `payments.adapters.cashfree.CashfreeAdapter` (disabled)
- `payments.adapters.razorpay.RazorpayAdapter` (disabled)
- Both adapters implement `PaymentGateway` interface
- Webhook handlers for payment verification
- Idempotency keys for safe retries

### Migration Strategy

1. Implement gateway adapters alongside manual adapter
2. Both adapters implement identical `PaymentGateway` interface
3. Switch via environment variable or feature flag
4. Run dual-mode for 30 days
5. Migrate owners gradually
6. Decommission manual adapter after 90 days of stable gateway operation

### Expected Trigger Point for Stage 2

- Monthly transaction volume exceeds 500 payments/month
- Manual verification overhead exceeds 10 hours/week
- Users request auto-payment features
