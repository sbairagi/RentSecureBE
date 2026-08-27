from __future__ import annotations

from rest_framework import serializers

from core.models import NotificationPreference, UserProfile
from notification.models import DeviceToken, Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "is_read",
            "read_at",
            "resource_type",
            "resource_id",
            "data",
            "priority",
            "channels",
            "action_url",
            "action_label",
            "image_url",
            "archived",
            "delivered_at",
            "created_at",
        ]
        read_only_fields = fields


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "user",
            "title",
            "message",
            "notification_type",
            "resource_type",
            "resource_id",
            "data",
            "priority",
            "channels",
            "action_url",
            "action_label",
            "image_url",
        ]
        read_only_fields = [
            "user",
        ]

    def create(self, validated_data):
        return Notification.objects.create(**validated_data)


class UnreadCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = [
            "id",
            "token",
            "device_id",
            "platform",
            "fcm_token",
            "active",
            "last_used",
            "created_at",
        ]
        read_only_fields = fields


class DeviceTokenCreateSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    device_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    platform = serializers.ChoiceField(
        choices=DeviceToken.PLATFORM_CHOICES, default="android"
    )
    fcm_token = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_token(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Token is required.")
        return value.strip()


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "push_enabled",
            "rent_alerts_push",
            "rent_alerts_whatsapp",
            "rent_alerts_email",
            "monthly_summary_email",
            "monthly_summary_whatsapp",
            "payout_alerts_whatsapp",
            "payout_alerts_email",
            "maintenance_push",
            "visitor_push",
            "agreement_push",
            "subscription_push",
            "system_push",
        ]
        read_only_fields = ["id"]


class NotificationPreferenceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "push_enabled",
            "rent_alerts_push",
            "rent_alerts_whatsapp",
            "rent_alerts_email",
            "monthly_summary_email",
            "monthly_summary_whatsapp",
            "payout_alerts_whatsapp",
            "payout_alerts_email",
            "maintenance_push",
            "visitor_push",
            "agreement_push",
            "subscription_push",
            "system_push",
        ]


class UserProfilePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "receive_rent_alerts",
            "receive_tax_alerts",
            "receive_vacancy_alerts",
            "receive_flagged_alerts",
            "receive_voice_alerts",
            "language_preference",
            "alert_frequency",
            "greeting_prefix",
            "reminder_time",
            "rent_reminders_enabled",
        ]
        read_only_fields = fields
