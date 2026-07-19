from django.urls import path

from payments.views.webhooks import cashfree_payout_webhook, razorpay_webhook

app_name = "payments"

urlpatterns = [
    path(
        "cashfree/payout/",
        cashfree_payout_webhook,
        name="cashfree_payout_webhook",
    ),
    path(
        "razorpay/",
        razorpay_webhook,
        name="razorpay_webhook",
    ),
]
