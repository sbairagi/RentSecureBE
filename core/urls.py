from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import include, path

from .views import (
    AddOnPurchaseViewSet,
    ChangePasswordView,
    OwnerVerifyOTP,
    RenterVerifyOTP,
    ResetPasswordView,
    SendOTP,
    SubscriptionPlanViewSet,
    UsageLimitViewSet,
    UserSubscriptionViewSet,
    cashfree_payout_webhook,
    razorpay_webhook,
    update_owner_bank_details,
)

# Subscription End-Points
router = DefaultRouter()
router.register(r"subscription-plans", SubscriptionPlanViewSet)
router.register(r"user-subscriptions", UserSubscriptionViewSet)
router.register(r"addon-purchases", AddOnPurchaseViewSet)
router.register(r"usage-limits", UsageLimitViewSet)
# router.register(r'plan-feature-limits', PlanFeatureLimitViewSet)


urlpatterns = [
    # comman auth end-points
    path("auth/send-otp/", SendOTP.as_view()),
    path("auth/owner/verify-otp/", OwnerVerifyOTP.as_view()),
    path("auth/renter/verify-otp/", RenterVerifyOTP.as_view()),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "webhook/cashfree/payout/",
        cashfree_payout_webhook,
        name="cashfree_payout_webhook",
    ),
    path("api/owner/update-bank-details/", update_owner_bank_details),
    path("api/rent/payment-callback/", razorpay_webhook),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("", include(router.urls)),
]

# urls.py


# urlpatterns = [

# ]
