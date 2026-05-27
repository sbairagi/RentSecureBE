from rest_framework import serializers

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
        fields = ['id', 'username', 'email', 'full_name', 'phone']



class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'user')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class AddOnPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddOnPurchase
        fields = '__all__'
        read_only_fields = ('user',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class PlanFeatureLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFeatureLimit
        fields = '__all__'

class UsageLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageLimit
        fields = '__all__'
