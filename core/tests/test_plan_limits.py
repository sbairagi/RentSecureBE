"""Tests for the canonical plan limits and the limit backfill migration."""

import importlib

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from core.plan_limits import (
    FREE_PLAN_LIMITS,
    PLAN_LIMITS,
    QUOTA_FEATURE_KEYS,
    is_raising_limit,
)
from properties.feature_enforcer import FeatureEnforcer

User = get_user_model()

MIGRATION_MODULE = "core.migrations.0006_sync_plan_feature_limits"


def apply_backfill():
    """Run the backfill migration body against the real model registry."""
    module = importlib.import_module(MIGRATION_MODULE)
    module.apply_canonical_limits(apps, None)


class PlanLimitCatalogueTests(TestCase):
    def test_every_plan_defines_every_quota_key(self):
        """A plan without a quota row resolves to a limit of 0."""
        for plan_name, limits in PLAN_LIMITS.items():
            for key in QUOTA_FEATURE_KEYS:
                self.assertIn(
                    key,
                    limits,
                    f"Plan '{plan_name}' is missing the quota key '{key}'.",
                )

    def test_free_plan_allows_more_than_one_agreement_draft(self):
        """Regression: the free plan shipped a limit of 1 draft."""
        limit = int(FREE_PLAN_LIMITS["rent_agreement_drafts"])
        self.assertGreater(limit, 1)

    def test_paid_plans_have_unlimited_agreement_drafts(self):
        for plan_name in ("pro", "elite"):
            self.assertEqual(
                PLAN_LIMITS[plan_name]["rent_agreement_drafts"], "unlimited"
            )

    def test_is_raising_limit_never_lowers_a_limit(self):
        self.assertTrue(is_raising_limit("1", "10"))
        self.assertTrue(is_raising_limit("10", "unlimited"))
        self.assertFalse(is_raising_limit("10", "5"))
        self.assertFalse(is_raising_limit("unlimited", "10"))
        self.assertFalse(is_raising_limit("unlimited", "unlimited"))


class PlanLimitResolutionTests(TestCase):
    def test_free_plan_resolves_a_usable_draft_limit(self):
        owner = User.objects.create_user(
            username="plan_free_owner", password="p", full_name="Free", phone="+1"
        )
        plan = SubscriptionPlan.objects.get(name="free")
        UserSubscription.objects.create(user=owner, plan=plan, is_active=True)
        for feature_key, value in FREE_PLAN_LIMITS.items():
            PlanFeatureLimit.objects.update_or_create(
                plan=plan, feature_key=feature_key, defaults={"value": value}
            )
        limit = FeatureEnforcer(owner).get_active_limit("rent_agreement_drafts")
        self.assertNotEqual(limit, 0)
        self.assertGreater(int(limit), 1)

    def test_plan_without_quota_row_blocks_the_workflow(self):
        """Documents the failure mode the catalogue protects against."""
        owner = User.objects.create_user(
            username="plan_bare_owner", password="p", full_name="Bare", phone="+2"
        )
        plan = SubscriptionPlan.objects.create(
            name="bare_plan",
            monthly_price="0",
            yearly_price="0",
            features="Bare",
            is_active=True,
        )
        UserSubscription.objects.create(user=owner, plan=plan, is_active=True)
        enforcer = FeatureEnforcer(owner)
        self.assertEqual(enforcer.get_active_limit("rent_agreement_drafts"), 0)
        self.assertFalse(enforcer.can_create("rent_agreement_drafts"))


class PlanLimitBackfillMigrationTests(TestCase):
    def setUp(self):
        self.free_plan, _ = SubscriptionPlan.objects.get_or_create(
            name="free",
            defaults={
                "monthly_price": "0",
                "yearly_price": "0",
                "features": "Free plan",
                "is_active": True,
            },
        )
        self.pro_plan, _ = SubscriptionPlan.objects.get_or_create(
            name="pro",
            defaults={
                "monthly_price": "29.99",
                "yearly_price": "299.99",
                "features": "Pro plan",
                "is_active": True,
            },
        )

    def test_backfill_raises_the_free_plan_draft_limit(self):
        PlanFeatureLimit.objects.update_or_create(
            plan=self.free_plan,
            feature_key="rent_agreement_drafts",
            defaults={"value": "1"},
        )
        apply_backfill()
        self.assertEqual(
            PlanFeatureLimit.objects.get(
                plan=self.free_plan, feature_key="rent_agreement_drafts"
            ).value,
            "10",
        )

    def test_backfill_creates_missing_quota_rows(self):
        apply_backfill()
        for key in QUOTA_FEATURE_KEYS:
            self.assertTrue(
                PlanFeatureLimit.objects.filter(
                    plan=self.pro_plan, feature_key=key
                ).exists(),
                f"Missing quota row '{key}' for the pro plan.",
            )

    def test_backfill_never_lowers_an_existing_limit(self):
        PlanFeatureLimit.objects.update_or_create(
            plan=self.free_plan,
            feature_key="max_buildings",
            defaults={"value": "unlimited"},
        )
        apply_backfill()
        self.assertEqual(
            PlanFeatureLimit.objects.get(
                plan=self.free_plan, feature_key="max_buildings"
            ).value,
            "unlimited",
        )
