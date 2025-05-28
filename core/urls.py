from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ( SubscriptionPlanViewSet, UserSubscriptionViewSet,
                    AddOnPurchaseViewSet, UsageLimitViewSet ) #ChangePasswordView, ResetPasswordView, PlanFeatureLimitViewSet
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .views import SendOTP, VerifyOTP

# Subscription End-Points
router = DefaultRouter()
router.register(r'subscription-plans', SubscriptionPlanViewSet)
router.register(r'user-subscriptions', UserSubscriptionViewSet)
router.register(r'addon-purchases', AddOnPurchaseViewSet)
router.register(r'usage-limits', UsageLimitViewSet)
# router.register(r'plan-feature-limits', PlanFeatureLimitViewSet)


urlpatterns = [
    # comman auth end-points
    path('auth/send-otp/', SendOTP.as_view()),
    path('auth/verify-otp/', VerifyOTP.as_view()),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    # path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),

    path('', include(router.urls)),
]