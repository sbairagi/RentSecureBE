from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import include, path
from django.views.generic import RedirectView

from .views.auth_views import (
    ChangePasswordView,
    OwnerVerifyOTP,
    RenterVerifyOTP,
    ResetPasswordView,
    SendOTP,
)
from .views.subscription_views import (
    AddOnPurchaseViewSet,
    SubscriptionPlanViewSet,
    UsageLimitViewSet,
    UserSubscriptionViewSet,
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
        RedirectView.as_view(url="/api/webhook/cashfree/payout/", permanent=True),
        name="cashfree_payout_webhook_redirect",
    ),
    path(
        "api/rent/payment-callback/",
        RedirectView.as_view(url="/api/webhook/razorpay/", permanent=True),
        name="razorpay_webhook_redirect",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("", include(router.urls)),
]
