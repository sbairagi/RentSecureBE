"""Comprehensive tests for FeatureEnforcer targeting all uncovered branches."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

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


class TestGetPlanName(TestCase):
    """Cover get_plan_name branches."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="gp_u1",
            email="gpu1@test.com",
            password="p",
            full_name="GP1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()

    def _create_plan(self, name="pro"):
        return SubscriptionPlan.objects.create(
            name=name,
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
            features="Pro",
            is_active=True,
        )

    def test_plan_is_none_returns_free(self):
        plan = self._create_plan()
        UserSubscription.objects.create(user=self.user, plan=plan)
        self.user.usersubscription.plan = None
        self.user.usersubscription.save(update_fields=["plan"])
        self.user.refresh_from_db()
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_plan_name(), "free")

    def test_user_subscription_does_not_exist(self):
        UserSubscription.objects.filter(user=self.user).delete()
        self.user.refresh_from_db()
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_plan_name(), "free")

    def test_attribute_error_returns_free(self):
        mock_user = MagicMock()
        del mock_user.usersubscription
        enforcer = FeatureEnforcer(mock_user)
        self.assertEqual(enforcer.get_plan_name(), "free")

    def test_normal_plan_returns_lowercase(self):
        plan = self._create_plan(name="pro")
        UserSubscription.objects.create(user=self.user, plan=plan)
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_plan_name(), "pro")


class TestCoerceDate(TestCase):
    """Cover _coerce_date branches."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="cd_u1",
            email="cdu1@test.com",
            password="p",
            full_name="CD1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()

    def test_none_returns_none(self):
        enforcer = FeatureEnforcer(self.user)
        self.assertIsNone(enforcer._coerce_date(None))

    def test_datetime_coerced_to_date(self):
        enforcer = FeatureEnforcer(self.user)
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = enforcer._coerce_date(dt)
        self.assertEqual(result, date(2024, 1, 15))

    def test_date_passthrough(self):
        enforcer = FeatureEnforcer(self.user)
        d = date(2024, 1, 15)
        result = enforcer._coerce_date(d)
        self.assertEqual(result, d)


class TestIsExpired(TestCase):
    """Cover is_expired branches."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="ie_u1",
            email="ieu1@test.com",
            password="p",
            full_name="IE1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()

    def _create_plan(self, name="pro"):
        return SubscriptionPlan.objects.create(
            name=name,
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
            features="Pro",
            is_active=True,
        )

    def test_user_subscription_does_not_exist(self):
        UserSubscription.objects.filter(user=self.user).delete()
        self.user.refresh_from_db()
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.is_expired())

    def test_end_date_none_not_expired(self):
        plan = self._create_plan()
        UserSubscription.objects.create(user=self.user, plan=plan, end_date=None)
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.is_expired())

    def test_future_end_date_not_expired(self):
        plan = self._create_plan()
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            end_date=timezone.now().date() + timedelta(days=30),
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.is_expired())

    def test_past_end_date_expired(self):
        plan = self._create_plan()
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            end_date=timezone.now().date() - timedelta(days=1),
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.is_expired())


class TestIsPastGracePeriod(TestCase):
    """Cover is_past_grace_period branches."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="gp_u1",
            email="gpu1@test.com",
            password="p",
            full_name="GP1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()

    def _create_plan(self, name="pro"):
        return SubscriptionPlan.objects.create(
            name=name,
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
            features="Pro",
            is_active=True,
        )

    def test_grace_days_none_uses_default(self):
        plan = self._create_plan()
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            end_date=timezone.now().date() - timedelta(days=10),
        )
        enforcer = FeatureEnforcer(self.user)
        # Just verify it works with default grace_days
        self.assertTrue(enforcer.is_past_grace_period())

    def test_user_subscription_does_not_exist(self):
        UserSubscription.objects.filter(user=self.user).delete()
        self.user.refresh_from_db()
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.is_past_grace_period())

    def test_end_date_none(self):
        plan = self._create_plan()
        UserSubscription.objects.create(user=self.user, plan=plan, end_date=None)
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.is_past_grace_period())

    def test_within_grace_period(self):
        plan = self._create_plan()
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            end_date=timezone.now().date() - timedelta(days=1),
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.is_past_grace_period(grace_days=7))

    def test_past_grace_period(self):
        plan = self._create_plan()
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            end_date=timezone.now().date() - timedelta(days=10),
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.is_past_grace_period(grace_days=7))

    def test_exact_grace_period_boundary(self):
        plan = self._create_plan()
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            end_date=timezone.now().date() - timedelta(days=7),
        )
        enforcer = FeatureEnforcer(self.user)
        # expired_since.days (7) > grace_days (7) is False
        self.assertFalse(enforcer.is_past_grace_period(grace_days=7))


class TestGetPlanLimit(TestCase):
    """Cover _get_plan_limit branches."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="gpl_u1",
            email="gplu1@test.com",
            password="p",
            full_name="GPL1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()

    def _create_plan(self, name="pro"):
        return SubscriptionPlan.objects.create(
            name=name,
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
            features="Pro",
            is_active=True,
        )

    def test_user_subscription_does_not_exist(self):
        UserSubscription.objects.filter(user=self.user).delete()
        self.user.refresh_from_db()
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer._get_plan_limit("max_buildings"), 0)

    def test_plan_is_none(self):
        plan = self._create_plan()
        UserSubscription.objects.create(user=self.user, plan=plan)
        self.user.usersubscription.plan = None
        self.user.usersubscription.save(update_fields=["plan"])
        self.user.refresh_from_db()
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer._get_plan_limit("max_buildings"), 0)

    def test_plan_feature_limit_does_not_exist(self):
        plan = self._create_plan()
        UserSubscription.objects.create(user=self.user, plan=plan)
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer._get_plan_limit("nonexistent_key"), 0)

    def test_unlimited_limit(self):
        plan = self._create_plan()
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_buildings", value="unlimited"
        )
        UserSubscription.objects.create(user=self.user, plan=plan)
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer._get_plan_limit("max_buildings"), "unlimited")

    def test_numeric_limit(self):
        plan = self._create_plan()
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_buildings", value="10"
        )
        UserSubscription.objects.create(user=self.user, plan=plan)
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer._get_plan_limit("max_buildings"), 10)

    def test_non_numeric_value_returns_zero(self):
        plan = self._create_plan()
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_buildings", value="not_numeric"
        )
        UserSubscription.objects.create(user=self.user, plan=plan)
        enforcer = FeatureEnforcer(self.user)
        with self.assertLogs("properties.feature_enforcer", level="WARNING") as cm:
            result = enforcer._get_plan_limit("max_buildings")
        self.assertEqual(result, 0)
        self.assertTrue(any("not numeric" in msg for msg in cm.output))


class TestGetFreePlanLimit(TestCase):
    """Cover _get_free_plan_limit branches."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="gfpl_u1",
            email="gfplu1@test.com",
            password="p",
            full_name="GFPL1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()
        # Clean up any auto-created plans/limits to have full control
        PlanFeatureLimit.objects.filter(plan__name="free").delete()
        SubscriptionPlan.objects.filter(name="free").delete()

    def test_subscription_plan_does_not_exist(self):
        SubscriptionPlan.objects.filter(name="free").delete()
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer._get_free_plan_limit("max_buildings"), 0)

    def test_plan_feature_limit_does_not_exist(self):
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        # Ensure no PlanFeatureLimit for max_buildings
        PlanFeatureLimit.objects.filter(
            plan=free_plan, feature_key="max_buildings"
        ).delete()
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer._get_free_plan_limit("max_buildings"), 0)

    def test_unlimited_free_plan(self):
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="unlimited"
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer._get_free_plan_limit("max_buildings"), "unlimited")

    def test_non_numeric_free_plan_value(self):
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="abc"
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer._get_free_plan_limit("max_buildings"), 0)

    def test_public_alias_get_free_plan_limit(self):
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="5"
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_free_plan_limit("max_buildings"), 5)


class TestGetActiveLimit(TestCase):
    """Cover get_active_limit branches."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="gal_u1",
            email="galu1@test.com",
            password="p",
            full_name="GAL1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()

    def _create_plan(self, name="pro"):
        return SubscriptionPlan.objects.create(
            name=name,
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
            features="Pro",
            is_active=True,
        )

    def test_user_subscription_does_not_exist(self):
        UserSubscription.objects.filter(user=self.user).delete()
        self.user.refresh_from_db()
        enforcer = FeatureEnforcer(self.user)
        # Falls back to free plan limit
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="2"
        )
        self.assertEqual(enforcer.get_active_limit("max_buildings"), 2)

    def test_expired_past_grace_returns_free(self):
        plan = self._create_plan()
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_buildings", value="20"
        )
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            end_date=timezone.now().date() - timedelta(days=30),
        )
        enforcer = FeatureEnforcer(self.user)
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="2"
        )
        self.assertEqual(enforcer.get_active_limit("max_buildings"), 2)

    def test_active_subscription_returns_plan_limit(self):
        plan = self._create_plan()
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_buildings", value="20"
        )
        UserSubscription.objects.create(user=self.user, plan=plan)
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_active_limit("max_buildings"), 20)

    def test_addon_extends_active_limit(self):
        plan = self._create_plan()
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_buildings", value="10"
        )
        UserSubscription.objects.create(user=self.user, plan=plan)
        AddOnPurchase.objects.create(
            user=self.user, name="max_buildings", amount=Decimal("5")
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_active_limit("max_buildings"), 15)

    def test_unlimited_plan_limit(self):
        plan = self._create_plan()
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_units", value="unlimited"
        )
        UserSubscription.objects.create(user=self.user, plan=plan)
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_active_limit("max_units"), "unlimited")


class TestCanCreate(TestCase):
    """Cover can_create branches."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="cc_u1",
            email="ccu1@test.com",
            password="p",
            full_name="CC1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()

    def _create_plan(self, name="pro"):
        return SubscriptionPlan.objects.create(
            name=name,
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
            features="Pro",
            is_active=True,
        )

    def test_unlimited_always_true(self):
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_units", value="unlimited"
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.can_create("max_units"))

    def test_no_usage_limit_under_limit(self):
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="2"
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.can_create("max_buildings"))

    def test_at_limit_returns_false(self):
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="2"
        )
        UsageLimit.objects.create(
            user=self.user, feature_key="max_buildings", usage_count=2
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.can_create("max_buildings"))

    def test_over_limit_returns_false(self):
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="2"
        )
        UsageLimit.objects.create(
            user=self.user, feature_key="max_buildings", usage_count=3
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertFalse(enforcer.can_create("max_buildings"))

    def test_under_limit_returns_true(self):
        free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            features="Free",
            is_active=True,
        )
        PlanFeatureLimit.objects.create(
            plan=free_plan, feature_key="max_buildings", value="2"
        )
        UsageLimit.objects.create(
            user=self.user, feature_key="max_buildings", usage_count=1
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.can_create("max_buildings"))


class TestIncrement(TestCase):
    """Cover increment behavior."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="inc_u1",
            email="incu1@test.com",
            password="p",
            full_name="INC1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()

    def test_increment_creates_new_usage_limit(self):
        enforcer = FeatureEnforcer(self.user)
        enforcer.increment("max_buildings")
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_buildings")
        self.assertEqual(ul.usage_count, 1)

    def test_increment_increments_existing(self):
        UsageLimit.objects.create(
            user=self.user, feature_key="max_buildings", usage_count=3
        )
        enforcer = FeatureEnforcer(self.user)
        enforcer.increment("max_buildings")
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_buildings")
        self.assertEqual(ul.usage_count, 4)


class TestDecrement(TestCase):
    """Cover decrement branches."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="dec_u1",
            email="decu1@test.com",
            password="p",
            full_name="DEC1",
            phone="+1",
        )
        UserSubscription.objects.filter(user=self.user).delete()

    def test_decrement_from_zero_stays_zero(self):
        enforcer = FeatureEnforcer(self.user)
        enforcer.decrement("max_buildings")
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_buildings")
        self.assertEqual(ul.usage_count, 0)

    def test_decrement_above_zero_decrements(self):
        UsageLimit.objects.create(
            user=self.user, feature_key="max_buildings", usage_count=3
        )
        enforcer = FeatureEnforcer(self.user)
        enforcer.decrement("max_buildings")
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_buildings")
        self.assertEqual(ul.usage_count, 2)

    def test_decrement_to_zero_saves(self):
        UsageLimit.objects.create(
            user=self.user, feature_key="max_buildings", usage_count=1
        )
        enforcer = FeatureEnforcer(self.user)
        enforcer.decrement("max_buildings")
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_buildings")
        self.assertEqual(ul.usage_count, 0)
