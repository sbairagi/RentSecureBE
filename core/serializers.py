from typing import Any, cast

from rest_framework import serializers

from rentsecure_be.type_compat import override

from .models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPayment,
    SubscriptionPlan,
    UsageLimit,
    User,
    UserSubscription,
)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "phone",
            "role",
            "permissions",
        ]

    def get_role(self, obj: User) -> str:
        group = obj.groups.first()
        return group.name if group else "user"

    def get_permissions(self, obj: User) -> list[str]:
        perms: set[str] = set()
        for group in obj.groups.all():
            perms.update(group.permissions.values_list("codename", flat=True))
        return sorted(perms)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    firstName = serializers.CharField()  # noqa: N815
    lastName = serializers.CharField()  # noqa: N815
    email = serializers.EmailField()
    phone = serializers.CharField()
    password = serializers.CharField()
    confirmPassword = serializers.CharField()  # noqa: N815
    role = serializers.ChoiceField(choices=["renter", "caretaker"])


class SocialAuthSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=["google", "apple"])
    token = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField()
    confirmPassword = serializers.CharField()  # noqa: N815


class DeviceInfoSerializer(serializers.Serializer):
    deviceId = serializers.CharField()  # noqa: N815
    deviceModel = serializers.CharField()  # noqa: N815
    deviceName = serializers.CharField()  # noqa: N815
    platform = serializers.ChoiceField(choices=["ios", "android", "web"])
    osVersion = serializers.CharField()  # noqa: N815
    appVersion = serializers.CharField()  # noqa: N815
    buildVersion = serializers.CharField()  # noqa: N815


class ProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "phone",
            "role",
            "permissions",
        ]

    def get_role(self, obj: User) -> str:
        group = obj.groups.first()
        return group.name if group else "user"

    def get_permissions(self, obj: User) -> list[str]:
        perms: set[str] = set()
        for group in obj.groups.all():
            perms.update(group.permissions.values_list("codename", flat=True))
        return sorted(perms)


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


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPayment
        fields = "__all__"
        read_only_fields = ("user", "created_at", "paid_at", "failed_at")

    @override
    def create(self, validated_data: dict[str, Any]) -> SubscriptionPayment:
        validated_data["user"] = self.context["request"].user
        return cast(SubscriptionPayment, super().create(validated_data))
