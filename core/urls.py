from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import include, path

from .views import (
    AddOnPurchaseViewSet,
    CaretakerVerifyOTP,
    ChangePasswordView,
    OwnerVerifyOTP,
    PlanFeatureLimitViewSet,
    RenterVerifyOTP,
    ResetPasswordView,
    SendEmailLink,
    SendOTP,
    SubscriptionPlanViewSet,
    UsageLimitViewSet,
    UserSubscriptionViewSet,
    VerifyEmailLink,
    app_version_view,
    bootstrap_view,
    cashfree_payout_webhook,
    login_view,
    logout_all_view,
    logout_view,
    maintenance_status_view,
    profile_view,
    razorpay_webhook,
    register_view,
    update_owner_bank_details,
)

# Subscription End-Points
router = DefaultRouter()
router.register(r"subscription-plans", SubscriptionPlanViewSet)
router.register(r"plan-feature-limits", PlanFeatureLimitViewSet)
router.register(r"user-subscriptions", UserSubscriptionViewSet)
router.register(r"addon-purchases", AddOnPurchaseViewSet)
router.register(r"usage-limits", UsageLimitViewSet)


urlpatterns = [
    # comman auth end-points
    path("auth/send-otp/", SendOTP.as_view()),
    path("auth/owner/verify-otp/", OwnerVerifyOTP.as_view()),
    path("auth/renter/verify-otp/", RenterVerifyOTP.as_view()),
    path("auth/caretaker/verify-otp/", CaretakerVerifyOTP.as_view()),
    path("auth/email-link/", SendEmailLink.as_view(), name="email-link"),
    path(
        "auth/email-link/verify/",
        VerifyEmailLink.as_view(),
        name="email-link-verify",
    ),
    path("auth/login/", login_view, name="login"),
    path("auth/register/", register_view, name="register"),
    path("auth/profile/", profile_view, name="profile"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/logout-all/", logout_all_view, name="logout-all"),
    path("auth/bootstrap/", bootstrap_view, name="bootstrap"),
    path("auth/maintenance/", maintenance_status_view, name="maintenance"),
    path("auth/app/version/", app_version_view, name="app-version"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "webhook/cashfree/payout/",
        cashfree_payout_webhook,
        name="cashfree_payout_webhook",
    ),
    path("owner/update-bank-details/", update_owner_bank_details),
    path("rent/payment-callback/", razorpay_webhook),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("", include(router.urls)),
]

# urls.py


# urlpatterns = [

# ]
