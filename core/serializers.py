from typing import Any, cast

from rest_framework import serializers

from rentsecure_be.type_compat import override

from .models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    User,
    UserSubscription,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "full_name", "phone"]


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at", "user")

    @override
    def create(self, validated_data: dict[str, Any]) -> UserSubscription:
        validated_data["user"] = self.context["request"].user
        user = validated_data.pop("user")
        subscription, _ = UserSubscription.objects.update_or_create(
            user=user,
            defaults=validated_data,
        )
        return subscription


class AddOnPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddOnPurchase
        fields = "__all__"
        read_only_fields = ("user",)

    @override
    def create(self, validated_data: dict[str, Any]) -> AddOnPurchase:
        validated_data["user"] = self.context["request"].user
        return cast(AddOnPurchase, super().create(validated_data))


class PlanFeatureLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFeatureLimit
        fields = "__all__"


class UsageLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageLimit
        fields = "__all__"
