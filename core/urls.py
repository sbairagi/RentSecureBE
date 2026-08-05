from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import include, path

from .views import (
    AddOnPurchaseViewSet,
    AppVersionView,
    BiometricDisableView,
    BiometricSetupView,
    BootstrapView,
    ChangePasswordView,
    DeviceRegisterView,
    LoginView,
    LogoutAllDevicesView,
    LogoutView,
    MaintenanceView,
    OwnerVerifyOTP,
    ProfileView,
    RegisterView,
    ReminderTimeUpdateView,
    RenterVerifyOTP,
    ResetPasswordView,
    SendOTP,
    SocialAuthView,
    SubscriptionPlanViewSet,
    UsageLimitViewSet,
    UserSubscriptionViewSet,
    cashfree_payout_webhook,
    download_ca_summary,
    download_rent_excel,
    download_tax_report,
    razorpay_webhook,
    tax_saving_tips,
    update_owner_alert_preferences,
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
    # common auth endpoints
    path("auth/send-otp/", SendOTP.as_view()),
    path("auth/owner/verify-otp/", OwnerVerifyOTP.as_view()),
    path("auth/renter/verify-otp/", RenterVerifyOTP.as_view()),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/social/", SocialAuthView.as_view(), name="social-auth"),
    path("auth/profile/", ProfileView.as_view(), name="profile"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/logout-all/", LogoutAllDevicesView.as_view(), name="logout-all"),
    path("auth/biometric/setup/", BiometricSetupView.as_view(), name="biometric-setup"),
    path(
        "auth/biometric/disable/",
        BiometricDisableView.as_view(),
        name="biometric-disable",
    ),
    path("auth/device/register/", DeviceRegisterView.as_view(), name="device-register"),
    path("auth/app/version/", AppVersionView.as_view(), name="app-version"),
    path("auth/maintenance/", MaintenanceView.as_view(), name="maintenance"),
    path("auth/bootstrap/", BootstrapView.as_view(), name="bootstrap"),
    path(
        "webhook/cashfree/payout/",
        cashfree_payout_webhook,
        name="cashfree_payout_webhook",
    ),
    path("api/owner/update-bank-details/", update_owner_bank_details),
    path("api/owner/update-alert-preferences/", update_owner_alert_preferences),
    path("api/owner/reminder-time/", ReminderTimeUpdateView.as_view()),
    path("api/rent/payment-callback/", razorpay_webhook),
    path("owner/rent-report/", download_rent_excel),
    path("owner/ca-summary/", download_ca_summary),
    path("tax/tax-report/", download_tax_report),
    path("tax/tax-saving-tips/", tax_saving_tips),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("", include(router.urls)),
]

# urls.py


# urlpatterns = [

# ]
