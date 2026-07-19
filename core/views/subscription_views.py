from __future__ import annotations

from typing import Any

from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth.models import AnonymousUser

from core.models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)
from core.serializers import (
    AddOnPurchaseSerializer,
    PlanFeatureLimitSerializer,
    SubscriptionPlanSerializer,
    UsageLimitSerializer,
    UserSubscriptionSerializer,
)
from core.services.subscription_service import SubscriptionService
from core.services.usage_limit_service import UsageLimitService


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class PlanFeatureLimitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlanFeatureLimit.objects.all()
    serializer_class = PlanFeatureLimitSerializer
    permission_classes = [permissions.AllowAny]


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> Any:
        if isinstance(self.request.user, AnonymousUser):
            return self.queryset.none()
        return SubscriptionService.get_user_subscriptions(self.request.user)

    def perform_create(self, serializer: Any) -> None:
        serializer.save(user=self.request.user)

    def perform_update(self, serializer: Any) -> None:
        subscription = serializer.instance
        if not SubscriptionService.can_user_modify(self.request.user, subscription):
            raise PermissionDenied("You can't edit another user's subscription.")
        serializer.save()

    def perform_destroy(self, instance: UserSubscription) -> None:
        if not SubscriptionService.can_user_modify(self.request.user, instance):
            raise PermissionDenied("You can't delete another user's subscription.")
        instance.delete()


class AddOnPurchaseViewSet(viewsets.ModelViewSet):
    queryset = AddOnPurchase.objects.all()
    serializer_class = AddOnPurchaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> Any:
        if isinstance(self.request.user, AnonymousUser):
            return self.queryset.none()
        return SubscriptionService.get_user_addon_purchases(self.request.user)

    def perform_create(self, serializer: Any) -> None:
        serializer.save(user=self.request.user)

    def perform_update(self, serializer: Any) -> None:
        purchase = serializer.instance
        if not SubscriptionService.can_user_modify(self.request.user, purchase):
            raise PermissionDenied("You can't modify another user's purchase.")
        serializer.save()

    def perform_destroy(self, instance: AddOnPurchase) -> None:
        if not SubscriptionService.can_user_modify(self.request.user, instance):
            raise PermissionDenied("You can't delete another user's purchase.")
        instance.delete()


class UsageLimitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UsageLimit.objects.all()
    serializer_class = UsageLimitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> Any:
        if isinstance(self.request.user, AnonymousUser):
            return self.queryset.none()
        return UsageLimitService.get_user_usage_limits(self.request.user)
