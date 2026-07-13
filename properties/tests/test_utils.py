"""Tests for properties/utils/utils.py — feature limit utilities, PDF generation, and late-fee logic."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from core.models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)
from properties.models import Building, Renter, RentRecord, Unit
from properties.utils.utils import (
    apply_late_fee_if_needed,
    check_feature_limit,
    deduct_feature_usage_with_priority,
    enforce_limit,
    generate_file_hash,
    generate_rent_invoice_pdf,
    get_feature_limit,
    get_limit_for_source,
    get_plan_limit,
    get_used_units,
    has_remaining_usage,
    update_usage_count,
)

User = get_user_model()


class GetPlanLimitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="planlimit", password="p", full_name="PlanLimit", phone="+1"
        )

    def test_anonymous_returns_none(self):
        result = get_plan_limit(AnonymousUser(), "max_units")
        self.assertIsNone(result)

    def test_no_subscription_returns_none(self):
        UserSubscription.objects.filter(user=self.user).delete()
        self.user.refresh_from_db()
        result = get_plan_limit(self.user, "max_units")
        self.assertIsNone(result)

    def test_no_plan_feature_limit_returns_none(self):
        plan = SubscriptionPlan.objects.create(
            name="noplan", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        result = get_plan_limit(self.user, "max_units")
        self.assertIsNone(result)

    def test_existing_limit_returns_value(self):
        plan = SubscriptionPlan.objects.create(
            name="hasplan", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="5")
        result = get_plan_limit(self.user, "max_units")
        self.assertEqual(result, "5")


class HasRemainingUsageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="hasusage", password="p", full_name="HasUsage", phone="+1"
        )

    def test_anonymous_returns_false(self):
        self.assertFalse(has_remaining_usage(AnonymousUser(), "max_units"))

    def test_unlimited_returns_true(self):
        plan = SubscriptionPlan.objects.create(
            name="hasusage_unlimited",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_units", value="unlimited"
        )
        self.assertTrue(has_remaining_usage(self.user, "max_units"))

    def test_no_limit_returns_false(self):
        plan = SubscriptionPlan.objects.create(
            name="hasusage_nolimit",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        self.assertFalse(has_remaining_usage(self.user, "max_units"))

    def test_within_limit_returns_true(self):
        plan = SubscriptionPlan.objects.create(
            name="hasusage_within",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="5")
        UsageLimit.objects.create(
            user=self.user, feature_key="max_units", usage_count=2
        )
        self.assertTrue(has_remaining_usage(self.user, "max_units"))

    def test_at_limit_returns_false(self):
        plan = SubscriptionPlan.objects.create(
            name="hasusage_atlimit",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="2")
        UsageLimit.objects.create(
            user=self.user, feature_key="max_units", usage_count=2
        )
        self.assertFalse(has_remaining_usage(self.user, "max_units"))


class UpdateUsageCountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="updateusage", password="p", full_name="UpdateUsage", phone="+1"
        )
        self.building = Building.objects.create(
            owner=self.user,
            name="UUB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="UU1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def test_anonymous_returns_early(self):
        update_usage_count(AnonymousUser(), "max_units", Unit)
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_units")
        self.assertEqual(ul.usage_count, 1)

    def test_unit_count_updates_usage(self):
        update_usage_count(self.user, "max_units", Unit)
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_units")
        self.assertEqual(ul.usage_count, 1)

    def test_building_count_updates_usage(self):
        update_usage_count(self.user, "max_buildings", Building)
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_buildings")
        self.assertEqual(ul.usage_count, 1)

    def test_renter_count_updates_usage(self):
        Renter.objects.create(
            unit=self.unit,
            name="UU Renter",
            phone="+911234567890",
            email="uu@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        update_usage_count(self.user, "max_renters", Renter)
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_renters")
        self.assertEqual(ul.usage_count, 1)


class EnforceLimitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="enforcelimit", password="p", full_name="EnforceLimit", phone="+1"
        )

    def test_anonymous_returns_early(self):
        enforce_limit(AnonymousUser(), "max_units")  # should not raise

    def test_no_subscription_raises(self):
        UserSubscription.objects.filter(user=self.user).delete()
        with self.assertRaises(PermissionDenied):
            enforce_limit(self.user, "max_units")

    def test_unlimited_returns_early(self):
        plan = SubscriptionPlan.objects.create(
            name="enforce_unlimited",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_units", value="unlimited"
        )
        enforce_limit(self.user, "max_units")  # should not raise

    def test_at_limit_raises(self):
        plan = SubscriptionPlan.objects.create(
            name="enforce_atlimit",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="1")
        UsageLimit.objects.create(
            user=self.user, feature_key="max_units", usage_count=1
        )
        with self.assertRaises(PermissionDenied):
            enforce_limit(self.user, "max_units")

    def test_feature_not_found_raises(self):
        plan = SubscriptionPlan.objects.create(
            name="enforce_notfound",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        with self.assertRaises(PermissionDenied):
            enforce_limit(self.user, "nonexistent_feature")


class CheckFeatureLimitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="checklimit", password="p", full_name="CheckLimit", phone="+1"
        )

    def test_no_subscription_returns_zero_limits(self):
        UserSubscription.objects.filter(user=self.user).delete()
        allowed, current, sub_limit, addon = check_feature_limit(self.user, "max_units")
        self.assertFalse(allowed)
        self.assertEqual(sub_limit, 0)

    def test_unlimited_returns_true(self):
        plan = SubscriptionPlan.objects.create(
            name="check_unlimited",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_units", value="unlimited"
        )
        allowed, current, sub_limit, addon = check_feature_limit(self.user, "max_units")
        self.assertTrue(allowed)
        self.assertEqual(sub_limit, "unlimited")

    def test_within_limit_returns_true(self):
        plan = SubscriptionPlan.objects.create(
            name="check_within", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="5")
        UsageLimit.objects.create(
            user=self.user, feature_key="max_units", usage_count=2
        )
        allowed, current, sub_limit, addon = check_feature_limit(self.user, "max_units")
        self.assertTrue(allowed)
        self.assertEqual(current, 2)

    def test_addon_extends_limit(self):
        plan = SubscriptionPlan.objects.create(
            name="check_addon", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="5")
        AddOnPurchase.objects.create(
            user=self.user, name="max_units", amount=Decimal("3")
        )
        allowed, current, sub_limit, addon = check_feature_limit(self.user, "max_units")
        self.assertTrue(allowed)
        self.assertEqual(addon, 3)


class GetFeatureLimitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="getlimit", password="p", full_name="GetLimit", phone="+1"
        )

    def test_no_pk_returns_zero(self):
        user = User(username="nopk")
        user.pk = None
        result = get_feature_limit(user, "max_units")
        self.assertEqual(result, 0)

    def test_unlimited_returns_inf(self):
        plan = SubscriptionPlan.objects.create(
            name="getlimit_unlimited",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_units", value="unlimited"
        )
        result = get_feature_limit(self.user, "max_units")
        self.assertEqual(result, float("inf"))


class GetLimitForSourceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="getlimit_user", password="p", full_name="GetLimitUser", phone="+1"
        )

    def test_user_subscription_returns_limit_value(self):
        plan = SubscriptionPlan.objects.create(
            name="gfsplan", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        sub = UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="10")
        result = get_limit_for_source(sub, "max_units")
        self.assertEqual(result, "10")

    def test_addon_with_features_returns_value(self):
        addon = AddOnPurchase.objects.create(
            user=self.user, name="max_units", amount=Decimal("5")
        )
        addon.features = {"max_units": 5}
        result = get_limit_for_source(addon, "max_units")
        self.assertEqual(result, 5)

    def test_addon_without_features_returns_zero(self):
        addon = AddOnPurchase.objects.create(
            user=self.user, name="max_units", amount=Decimal("5")
        )
        result = get_limit_for_source(addon, "max_units")
        self.assertEqual(result, 0)


class GetUsedUnitsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="getusedunits", password="p", full_name="GetUsedUnits", phone="+1"
        )

    def test_no_pk_returns_zero(self):
        user = User(username="nopk2")
        user.pk = None
        plan = SubscriptionPlan.objects.create(
            name="guuplan", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        UserSubscription(user=user, plan=plan, is_active=True)
        result = get_used_units(user, "max_units")
        self.assertEqual(result, 0)

    def test_usage_limit_count_returned(self):
        plan = SubscriptionPlan.objects.create(
            name="guuplan2", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        UsageLimit.objects.create(
            user=self.user, feature_key="max_units", usage_count=3
        )
        result = get_used_units(self.user, "max_units")
        self.assertEqual(result, 3)


class DeductFeatureUsageWithPriorityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="deduct", password="p", full_name="Deduct", phone="+1"
        )

    def test_insufficient_raises_validation_error(self):
        plan = SubscriptionPlan.objects.create(
            name="deduct", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="0")
        with self.assertRaises(ValidationError):
            deduct_feature_usage_with_priority(self.user, "max_units")

    def test_successful_deduct_increments(self):
        plan = SubscriptionPlan.objects.create(
            name="deduct2", monthly_price=Decimal("0"), yearly_price=Decimal("0")
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="5")
        deduct_feature_usage_with_priority(self.user, "max_units")
        ul = UsageLimit.objects.get(user=self.user, feature_key="max_units")
        self.assertEqual(ul.usage_count, 1)


class ApplyLateFeeIfNeededTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="latefee_owner", password="p", full_name="LFOwner", phone="+1"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="LFB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="LF1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.renter = Renter.objects.create(
            unit=cls.unit,
            name="LF Renter",
            phone="+911234567890",
            email="lf@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )

    def test_not_paid_returns_early(self):
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("1000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today(),
            late_fee=Decimal("0"),
            discount=Decimal("0"),
        )
        apply_late_fee_if_needed(rent)
        rent.refresh_from_db()
        self.assertEqual(rent.late_fee, Decimal("0"))

    def test_paid_on_time_returns_early(self):
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("1000"),
            payment_method="upi",
            status=RentRecord.Status.PAID.value,
            paid_on=date.today() - timedelta(days=1),
            due_date=date.today(),
            late_fee=Decimal("0"),
            discount=Decimal("0"),
        )
        apply_late_fee_if_needed(rent)
        rent.refresh_from_db()
        self.assertEqual(rent.late_fee, Decimal("0"))

    def test_late_payment_applies_fee(self):
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("1000"),
            payment_method="upi",
            status=RentRecord.Status.PAID.value,
            paid_on=date.today() + timedelta(days=5),
            due_date=date.today(),
            late_fee=Decimal("0"),
            discount=Decimal("0"),
            notes="",
        )
        with (
            patch(
                "properties.utils.utils.notify_renter_about_late_fee"
            ) as mock_notify_renter,
            patch(
                "properties.utils.utils.notify_owner_about_late_fee"
            ) as mock_notify_owner,
        ):
            apply_late_fee_if_needed(rent)
        rent.refresh_from_db()
        self.assertEqual(rent.late_fee, Decimal("500"))
        self.assertIn("5 days late", rent.notes)
        mock_notify_renter.assert_called_once()
        mock_notify_owner.assert_called_once()

    def test_idempotent_on_second_call(self):
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("1000"),
            payment_method="upi",
            status=RentRecord.Status.PAID.value,
            paid_on=date.today() + timedelta(days=3),
            due_date=date.today(),
            late_fee=Decimal("0"),
            discount=Decimal("0"),
            notes="",
        )
        with (
            patch(
                "properties.utils.utils.notify_renter_about_late_fee"
            ) as mock_notify_renter,
            patch(
                "properties.utils.utils.notify_owner_about_late_fee"
            ) as mock_notify_owner,
        ):
            apply_late_fee_if_needed(rent)
            apply_late_fee_if_needed(rent)
        rent.refresh_from_db()
        self.assertEqual(rent.late_fee, Decimal("300"))
        self.assertEqual(mock_notify_renter.call_count, 2)
        self.assertEqual(mock_notify_owner.call_count, 2)


# ---------------------------------------------------------------------------
# Additional edge-case tests to reach ≥95% coverage of properties/utils/utils.py
# ---------------------------------------------------------------------------


class TestHasRemainingUsageEdgeCases(TestCase):
    """Cover lines 64-65: TypeError/ValueError and UsageLimit.DoesNotExist."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="hasusage_edge", password="p", full_name="HasUsageEdge", phone="+1"
        )

    def test_non_numeric_plan_limit_returns_false(self):
        plan = SubscriptionPlan.objects.create(
            name="hasusage_invalid",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="abc")
        self.assertFalse(has_remaining_usage(self.user, "max_units"))

    def test_numeric_plan_limit_no_usage_limit_returns_false(self):
        plan = SubscriptionPlan.objects.create(
            name="hasusage_numeric_nousage",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="5")
        self.assertFalse(has_remaining_usage(self.user, "max_units"))


class TestEnforceLimitEdgeCases(TestCase):
    """Cover line 127 ('no' value) and line 131->exit (non-numeric int() failure)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="enforce_edge", password="p", full_name="EnforceEdge", phone="+1"
        )

    def test_feature_disabled_raises_permission_denied(self):
        plan = SubscriptionPlan.objects.create(
            name="enforce_no",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="no")
        with self.assertRaises(PermissionDenied):
            enforce_limit(self.user, "max_units")

    def test_non_numeric_limit_propagates_value_error(self):
        plan = SubscriptionPlan.objects.create(
            name="enforce_invalid",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="abc")
        with self.assertRaises(ValueError):
            enforce_limit(self.user, "max_units")


class TestGenerateFileHash(TestCase):
    """Cover lines 139-142: generate_file_hash body."""

    def test_returns_sha256_hex(self):
        mock_file = MagicMock()
        mock_file.chunks.return_value = [b"hello world"]
        result = generate_file_hash(mock_file)
        self.assertEqual(len(result), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))


class TestGenerateRentInvoicePdf(TestCase):
    """Cover lines 146-153: generate_rent_invoice_pdf body."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="pdf_owner", password="p", full_name="PdfOwner", phone="+1"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="PDFB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="PDF1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.renter = Renter.objects.create(
            unit=cls.unit,
            name="PDF Renter",
            phone="+911234567890",
            email="pdf@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        cls.rent = RentRecord.objects.create(
            unit=cls.unit,
            renter=cls.renter,
            amount=Decimal("1000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today(),
            late_fee=Decimal("0"),
            discount=Decimal("0"),
        )

    @patch("properties.utils.utils.render_to_string")
    @patch("weasyprint.HTML")
    def test_returns_pdf_path(self, mock_html_cls, mock_render):
        mock_render.return_value = "<html>invoice</html>"
        mock_html = MagicMock()
        mock_html_cls.return_value = mock_html

        mock_tmp_file = MagicMock()
        mock_tmp_file.name = "/tmp/test_invoice.pdf"

        with patch("tempfile.NamedTemporaryFile") as mock_tmp:
            mock_tmp.return_value = mock_tmp_file
            result = generate_rent_invoice_pdf(self.rent)

        self.assertTrue(result.endswith(".pdf"))
        mock_html.write_pdf.assert_called_once_with(target=result)


class TestCheckFeatureLimitEdgeCases(TestCase):
    """Cover line 195->200: plan_limit is None (subscription exists, no PlanFeatureLimit)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="check_edge", password="p", full_name="CheckEdge", phone="+1"
        )

    def test_subscription_without_plan_limit_returns_zero(self):
        plan = SubscriptionPlan.objects.create(
            name="check_nolimit",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        # No PlanFeatureLimit for this feature
        allowed, current, sub_limit, addon = check_feature_limit(self.user, "max_units")
        self.assertEqual(sub_limit, 0)
        self.assertFalse(allowed)


class TestGetFeatureLimitEdgeCases(TestCase):
    """Cover lines 229 and 236 in get_feature_limit."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="getlimit_edge", password="p", full_name="GetLimitEdge", phone="+1"
        )

    def test_usage_limit_exists_returns_count(self):
        plan = SubscriptionPlan.objects.create(
            name="getlimit_usage",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        UsageLimit.objects.create(
            user=self.user, feature_key="max_units", usage_count=7
        )
        result = get_feature_limit(self.user, "max_units")
        self.assertEqual(result, 7)

    def test_no_usage_limit_no_plan_limit_returns_zero(self):
        plan = SubscriptionPlan.objects.create(
            name="getlimit_none",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        # No UsageLimit and no PlanFeatureLimit
        result = get_feature_limit(self.user, "max_units")
        self.assertEqual(result, 0)


class TestGetLimitForSourceEdgeCases(TestCase):
    """Cover lines 252->254: addon_value is not int or str."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="getlimit_user_edge",
            password="p",
            full_name="GetLimitUserEdge",
            phone="+1",
        )

    def test_addon_with_non_int_str_feature_returns_zero(self):
        addon = AddOnPurchase.objects.create(
            user=self.user, name="max_units", amount=Decimal("5")
        )
        addon.features = {"max_units": [1, 2, 3]}
        result = get_limit_for_source(addon, "max_units")
        self.assertEqual(result, 0)


class TestDeductFeatureUsageWithPriorityEdgeCases(TestCase):
    """Cover line 288: ValidationError raised inside the for-loop on second iteration."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="deduct_edge", password="p", full_name="DeductEdge", phone="+1"
        )

    def test_deduct_more_than_available_raises(self):
        plan = SubscriptionPlan.objects.create(
            name="deduct_insufficient",
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
        )
        UserSubscription.objects.create(user=self.user, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="1")
        with self.assertRaises(ValidationError):
            deduct_feature_usage_with_priority(
                self.user, "max_units", units_to_deduct=2
            )
