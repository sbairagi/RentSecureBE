"""Edge case tests for FeatureEnforcer covering remaining uncovered lines"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)
from properties.feature_enforcer import FeatureEnforcer

User = get_user_model()


class FeatureEnforcerEdgeCases(TestCase):
    """Covers remaining feature_enforcer.py lines"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="fee_u1",
            email="feeu1@test.com",
            password="p",
            full_name="FEE1",
            phone="+1",
        )
        # Signal creates a UserSubscription with a free plan. Delete auto-created one to have clean state.
        UserSubscription.objects.filter(user=self.user).delete()
        self.free_plan = SubscriptionPlan.objects.get_or_create(
            name="free",
            defaults={
                "monthly_price": Decimal("0"),
                "yearly_price": Decimal("0"),
                "features": "Free",
                "is_active": True,
            },
        )[0]
        PlanFeatureLimit.objects.create(
            plan=self.free_plan, feature_key="max_buildings", value="2"
        )
        PlanFeatureLimit.objects.create(
            plan=self.free_plan, feature_key="max_units", value="unlimited"
        )

    def _create_sub(self, plan, **kwargs):
        """Helper to create subscription, cleaning up auto-created one first."""
        UserSubscription.objects.filter(user=self.user).delete()
        return UserSubscription.objects.create(user=self.user, plan=plan, **kwargs)

    def test_get_active_limit_no_subscription(self):
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_active_limit("max_buildings"), 2)

    def test_get_active_limit_unlimited(self):
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_active_limit("max_units"), "unlimited")

    def test_get_active_limit_expired_no_grace(self):
        pro = SubscriptionPlan.objects.create(
            name="pro",
            monthly_price=Decimal("499"),
            yearly_price=Decimal("4999"),
            features="Pro",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=pro, feature_key="max_buildings", value="20"
        )
        self._create_sub(pro, end_date=timezone.now() - timedelta(days=10))
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_active_limit("max_buildings"), 2)

    def test_get_active_limit_within_grace(self):
        pro = SubscriptionPlan.objects.create(
            name="pro2",
            monthly_price=Decimal("499"),
            yearly_price=Decimal("4999"),
            features="Pro2",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=pro, feature_key="max_buildings", value="20"
        )
        self._create_sub(pro, end_date=timezone.now() - timedelta(days=1))
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_active_limit("max_buildings"), 20)

    def test_can_create_under_limit(self):
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.can_create("max_buildings"))

    def test_can_create_at_limit(self):
        UsageLimit.objects.create(
            user=self.user, feature_key="max_buildings", usage_count=2
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.can_create("max_buildings"))

    def test_can_create_unlimited(self):
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.can_create("max_units"))

    def test_increment_creates_usage_limit(self):
        enforcer = FeatureEnforcer(self.user)
        enforcer.increment("max_buildings")
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_buildings")
        self.assertEqual(ul.usage_count, 1)

    def test_decrement_does_not_go_below_zero(self):
        enforcer = FeatureEnforcer(self.user)
        enforcer.decrement("max_buildings")
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_buildings")
        self.assertEqual(ul.usage_count, 0)
        enforcer.decrement("max_buildings")
        ul.refresh_from_db()
        self.assertEqual(ul.usage_count, 0)

    def test_addon_extends_limit(self):
        pro = SubscriptionPlan.objects.create(
            name="pro3",
            monthly_price=Decimal("499"),
            yearly_price=Decimal("4999"),
            features="Pro3",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=pro, feature_key="max_buildings", value="10"
        )
        self._create_sub(pro)
        AddOnPurchase.objects.create(
            user=self.user, name="max_buildings", amount=Decimal("5")
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_active_limit("max_buildings"), 15)

    def test_plan_with_subscription_but_no_limit_returns_zero(self):
        pro = SubscriptionPlan.objects.create(
            name="pro_limitless",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Pro",
            is_active=True,
        )
        self._create_sub(pro)
        enforcer = FeatureEnforcer(self.user)
        limit = enforcer._get_plan_limit("nonexistent_key")
        self.assertEqual(limit, 0)

    def test_user_subscription_does_not_exist_returns_free(self):
        UserSubscription.objects.filter(user=self.user).delete()
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_plan_name(), "free")

    def test_is_expired_with_subscription_no_end_date(self):
        pro = SubscriptionPlan.objects.create(
            name="pro4",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Pro4",
            is_active=True,
        )
        self._create_sub(pro, end_date=None)
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.is_expired())

    def test_is_expired_with_subscription_future_end(self):
        pro = SubscriptionPlan.objects.create(
            name="pro5",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Pro5",
            is_active=True,
        )
        self._create_sub(pro, end_date=timezone.now() + timedelta(days=30))
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.is_expired())

    def test_is_expired_with_subscription_past_end(self):
        pro = SubscriptionPlan.objects.create(
            name="pro6",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Pro6",
            is_active=True,
        )
        self._create_sub(pro, end_date=timezone.now() - timedelta(days=1))
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.is_expired())

    def test_is_past_grace_period_with_subscription_no_end(self):
        pro = SubscriptionPlan.objects.create(
            name="pro7",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Pro7",
            is_active=True,
        )
        self._create_sub(pro, end_date=None)
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.is_past_grace_period())
