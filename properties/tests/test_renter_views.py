"""Comprehensive pytest tests for properties/views/renter_views.py."""

from decimal import Decimal
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.utils import timezone

from core.models import PlanFeatureLimit, SubscriptionPlan, UsageLimit, UserSubscription
from properties.models import Building, Renter, Unit
from properties.views.renter_views import RenterViewSet

User = get_user_model()


def _auth(u):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
    return c


class RenterViewSetGetQuerysetTests(TestCase):
    """Cover get_queryset anonymous-user branch, cache-miss branch, and cache-hit branch."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rv_gq_owner",
            password="p",
            full_name="RvGQOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rv_gq_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RvGQB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        cache.clear()

    def test_anonymous_user_queryset_returns_empty(self):
        request = RequestFactory().get("/properties/renters/")
        request.user = AnonymousUser()
        view = RenterViewSet()
        view.request = request
        view.format_kwarg = None
        self.assertEqual(list(view.get_queryset()), [])

    def test_authenticated_owner_cache_miss_fetches_and_caches(self):
        unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="RVGQ1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        renter = Renter.objects.create(
            unit=unit,
            name="CacheMissRenter",
            phone="+911234567901",
            email="cmr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
            is_active=True,
        )
        cache_key = f"renters_user_{self.owner.id}"
        self.assertIsNone(cache.get(cache_key))

        request = RequestFactory().get("/properties/renters/")
        request.user = self.owner
        view = RenterViewSet()
        view.request = request
        view.format_kwarg = None

        qs = view.get_queryset()
        self.assertEqual(list(qs), [renter])
        self.assertIsNotNone(cache.get(cache_key))

    def test_authenticated_owner_cache_hit_returns_cached(self):
        unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="RVGQ2",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        renter = Renter.objects.create(
            unit=unit,
            name="CacheHitRenter",
            phone="+911234567902",
            email="chr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
            is_active=True,
        )
        cache_key = f"renters_user_{self.owner.id}"
        cache.set(cache_key, [renter], timeout=300)

        request = RequestFactory().get("/properties/renters/")
        request.user = self.owner
        view = RenterViewSet()
        view.request = request
        view.format_kwarg = None

        qs = view.get_queryset()
        self.assertEqual(list(qs), [renter])

    def test_list_endpoint_returns_own_renters(self):
        unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="RVGQ3",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        Renter.objects.create(
            unit=unit,
            name="ListRenter",
            phone="+911234567903",
            email="lr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
            is_active=True,
        )
        response = _auth(self.owner).get("/properties/renters/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class RenterViewSetCreateLimitTests(TestCase):
    """Cover create() feature-limit exceeded branch."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rv_cl_owner",
            password="p",
            full_name="RvCLOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rv_cl_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_renters", value="1"
        )
        UsageLimit.objects.create(
            user=cls.owner, feature_key="max_renters", usage_count=1
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RvCLB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RVCL1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        cache.clear()

    def test_create_renter_limit_exceeded_returns_403(self):
        response = _auth(self.owner).post(
            "/properties/renters/",
            {
                "unit": self.unit.id,
                "name": "LimitExceededRenter",
                "email": "ler@test.com",
                "phone": "+911234567901",
                "rent_amount": "10000",
                "start_date": str(timezone.now().date()),
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.data)


class RenterViewSetPerformCreateTests(TestCase):
    """Cover perform_create owner-mismatch and enforcer-limit branches."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rv_pc_owner",
            password="p",
            full_name="RvPCOwner",
            phone="+1",
        )
        cls.attacker = User.objects.create_user(
            username="rv_pc_attacker",
            password="p",
            full_name="RvPCAttacker",
            phone="+2",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rv_pc_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_renters", value="10"
        )
        UsageLimit.objects.create(
            user=cls.owner, feature_key="max_renters", usage_count=0
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RvPCB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.owner_unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RVPC1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.attacker_building = Building.objects.create(
            owner=cls.attacker,
            name="RvPCAttackerB",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        cls.attacker_unit = Unit.objects.create(
            owner=cls.attacker,
            building=cls.attacker_building,
            unit="RVPC2",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )

    def setUp(self):
        cache.clear()

    def _make_view(self, user):
        request = RequestFactory().post("/properties/renters/")
        request.user = user
        view = RenterViewSet()
        view.request = request
        view.format_kwarg = None
        return view

    def test_perform_create_wrong_unit_owner_raises_permission_denied(self):
        from rest_framework.exceptions import PermissionDenied

        view = self._make_view(self.owner)
        serializer = type(
            "Ser",
            (),
            {
                "validated_data": {"unit": self.attacker_unit},
                "save": lambda *a, **kw: None,
            },
        )()
        with self.assertRaises(PermissionDenied):
            view.perform_create(serializer)

    def test_perform_create_unit_none_raises_permission_denied(self):
        from rest_framework.exceptions import PermissionDenied

        view = self._make_view(self.owner)
        serializer = type(
            "Ser",
            (),
            {
                "validated_data": {"unit": None},
                "save": lambda *a, **kw: None,
            },
        )()
        with self.assertRaises(PermissionDenied):
            view.perform_create(serializer)

    def test_perform_create_enforcer_limit_reached_raises_permission_denied(self):
        from rest_framework.exceptions import PermissionDenied

        UsageLimit.objects.filter(user=self.owner, feature_key="max_renters").update(
            usage_count=10
        )
        view = self._make_view(self.owner)
        serializer = type(
            "Ser",
            (),
            {
                "validated_data": {"unit": self.owner_unit},
                "save": lambda *a, **kw: None,
            },
        )()
        with self.assertRaises(PermissionDenied):
            view.perform_create(serializer)

    @patch("properties.views.renter_views.update_unit_status")
    def test_perform_create_happy_path(self, mock_update_unit_status):
        view = self._make_view(self.owner)
        renter = Renter.objects.create(
            unit=self.owner_unit,
            name="HappyRenter",
            phone="+911234567901",
            email="hr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )
        serializer = type(
            "Ser",
            (),
            {
                "validated_data": {"unit": self.owner_unit},
                "save": lambda *a, **kw: renter,
            },
        )()
        view.perform_create(serializer)
        self.assertTrue(
            Renter.objects.filter(id=renter.id, unit=self.owner_unit).exists()
        )
        mock_update_unit_status.assert_called_once_with(self.owner_unit)
        cache_key = f"renters_user_{self.owner.id}"
        self.assertIsNone(cache.get(cache_key))


class RenterViewSetPerformUpdateTests(TestCase):
    """Cover perform_update owner-mismatch branch and happy path."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rv_pu_owner",
            password="p",
            full_name="RvPUOwner",
            phone="+1",
        )
        cls.attacker = User.objects.create_user(
            username="rv_pu_attacker",
            password="p",
            full_name="RvPUAttacker",
            phone="+2",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rv_pu_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RvPUB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.owner_unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RVPU1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.attacker_building = Building.objects.create(
            owner=cls.attacker,
            name="RvPUAttackerB",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        cls.attacker_unit = Unit.objects.create(
            owner=cls.attacker,
            building=cls.attacker_building,
            unit="RVPU2",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )

    def setUp(self):
        cache.clear()

    def _make_view(self, user):
        request = RequestFactory().patch("/properties/renters/")
        request.user = user
        view = RenterViewSet()
        view.request = request
        view.format_kwarg = None
        return view

    def test_perform_update_wrong_unit_owner_raises_permission_denied(self):
        from rest_framework.exceptions import PermissionDenied

        renter = Renter.objects.create(
            unit=self.owner_unit,
            name="UpdRenter",
            phone="+911234567901",
            email="updr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )
        view = self._make_view(self.owner)
        serializer = type(
            "Ser",
            (),
            {
                "instance": renter,
                "validated_data": {"unit": self.attacker_unit},
                "save": lambda *a, **kw: None,
            },
        )()
        with self.assertRaises(PermissionDenied):
            view.perform_update(serializer)

    def test_perform_update_instance_none_raises_permission_denied(self):
        from rest_framework.exceptions import PermissionDenied

        view = self._make_view(self.owner)
        serializer = type(
            "Ser",
            (),
            {
                "instance": None,
                "validated_data": {},
                "save": lambda *a, **kw: None,
            },
        )()
        with self.assertRaises(PermissionDenied):
            view.perform_update(serializer)

    @patch("properties.views.renter_views.update_unit_status")
    def test_perform_update_happy_path(self, mock_update_unit_status):
        renter = Renter.objects.create(
            unit=self.owner_unit,
            name="UpdHappyRenter",
            phone="+911234567902",
            email="uphr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )
        view = self._make_view(self.owner)
        serializer = type(
            "Ser",
            (),
            {
                "instance": renter,
                "validated_data": {"unit": self.owner_unit},
                "save": lambda *a, **kw: renter,
            },
        )()
        view.perform_update(serializer)
        mock_update_unit_status.assert_called_once_with(self.owner_unit)
        cache_key = f"renters_user_{self.owner.id}"
        self.assertIsNone(cache.get(cache_key))


class RenterViewSetPerformDestroyTests(TestCase):
    """Cover perform_destroy owner-mismatch branch and happy path."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rv_pd_owner",
            password="p",
            full_name="RvPDOwner",
            phone="+1",
        )
        cls.attacker = User.objects.create_user(
            username="rv_pd_attacker",
            password="p",
            full_name="RvPDAttacker",
            phone="+2",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rv_pd_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_renters", value="10"
        )
        UsageLimit.objects.create(
            user=cls.owner, feature_key="max_renters", usage_count=0
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RvPDB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.owner_unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RVPD1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.attacker_building = Building.objects.create(
            owner=cls.attacker,
            name="RvPDAttackerB",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        cls.attacker_unit = Unit.objects.create(
            owner=cls.attacker,
            building=cls.attacker_building,
            unit="RVPD2",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )

    def setUp(self):
        cache.clear()

    def _make_view(self, user):
        request = RequestFactory().delete("/properties/renters/")
        request.user = user
        view = RenterViewSet()
        view.request = request
        view.format_kwarg = None
        return view

    def test_perform_destroy_wrong_unit_owner_raises_permission_denied(self):
        from rest_framework.exceptions import PermissionDenied

        attacker_renter = Renter.objects.create(
            unit=self.attacker_unit,
            name="AttackerRenter",
            phone="+911234567901",
            email="ar@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )
        view = self._make_view(self.owner)
        with self.assertRaises(PermissionDenied):
            view.perform_destroy(attacker_renter)

    @patch("properties.views.renter_views.update_unit_status")
    def test_perform_destroy_happy_path_decrements_and_deletes(
        self, mock_update_unit_status
    ):
        renter = Renter.objects.create(
            unit=self.owner_unit,
            name="DelRenter",
            phone="+911234567902",
            email="delr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )
        UsageLimit.objects.create(
            user=self.owner, feature_key="max_renters", usage_count=1
        )
        view = self._make_view(self.owner)
        view.perform_destroy(renter)
        self.assertFalse(Renter.objects.filter(id=renter.id).exists())
        usage = UsageLimit.objects.get(user=self.owner, feature_key="max_renters")
        self.assertEqual(usage.usage_count, 0)
        mock_update_unit_status.assert_called_once_with(self.owner_unit)
        cache_key = f"renters_user_{self.owner.id}"
        self.assertIsNone(cache.get(cache_key))


class RenterViewSetIntegrationTests(TestCase):
    """API-level integration tests covering update and delete happy paths."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rv_int_owner",
            password="p",
            full_name="RvIntOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rv_int_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_renters", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RvIntB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RVINT1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_update_renter_returns_200(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="UpdRenter",
            phone="+911234567901",
            email="updr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )
        response = self._c.patch(
            f"/properties/renters/{renter.id}/",
            {"name": "UpdatedRenter"},
        )
        self.assertEqual(response.status_code, 200)
        renter.refresh_from_db()
        self.assertEqual(renter.name, "UpdatedRenter")

    def test_delete_renter_returns_204(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="DelRenter",
            phone="+911234567902",
            email="delr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )
        response = self._c.delete(f"/properties/renters/{renter.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Renter.objects.filter(id=renter.id).exists())

    def test_create_renter_succeeds_when_allowed(self):
        response = self._c.post(
            "/properties/renters/",
            {
                "unit": self.unit.id,
                "name": "NewRenter",
                "email": "nr@test.com",
                "phone": "+911234567901",
                "rent_amount": "10000",
                "start_date": str(timezone.now().date()),
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Renter.objects.filter(name="NewRenter").exists())


class RenterViewSetSubmitRatingTests(TestCase):
    """Cover submit_rating action."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rv_rate_owner",
            password="p",
            full_name="RvRateOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rv_rate_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RvRateB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RVRATE1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_active_renter_cannot_rate(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="ActiveRenter",
            phone="+911234567901",
            email="activer@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/rate/",
            {"rating": 5, "feedback": "good"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        renter.refresh_from_db()
        self.assertIsNone(renter.rating)

    def test_deactivated_renter_can_rate(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="DeactivatedRenter",
            phone="+911234567901",
            email="deactr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.DEACTIVATED,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/rate/",
            {"rating": 4, "feedback": "nice stay"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renter.refresh_from_db()
        self.assertEqual(renter.rating, 4)
        self.assertEqual(renter.feedback, "nice stay")
        self.assertIsNotNone(renter.rated_at)

    def test_revoked_renter_can_rate(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="RevokedRenter",
            phone="+911234567901",
            email="revokedr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.REVOKED,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/rate/",
            {"rating": 3, "feedback": "ok"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renter.refresh_from_db()
        self.assertEqual(renter.rating, 3)

    def test_notice_period_renter_can_rate(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="NoticeRenter",
            phone="+911234567901",
            email="noticer@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.NOTICE_PERIOD,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/rate/",
            {"rating": 5, "feedback": "great"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renter.refresh_from_db()
        self.assertEqual(renter.rating, 5)

    def test_missing_rating_returns_400(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="NoRatingRenter",
            phone="+911234567901",
            email="norating@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.DEACTIVATED,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/rate/",
            {"feedback": "no rating"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_rating_out_of_range_returns_400(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="BadRatingRenter",
            phone="+911234567901",
            email="badrating@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.DEACTIVATED,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/rate/",
            {"rating": 6},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RenterAssignUnitTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="assign_unit_owner",
            password="p",
            full_name="AssignUnitOwner",
            phone="+1",
        )
        cls.other = User.objects.create_user(
            username="assign_unit_other",
            password="p",
            full_name="AssignUnitOther",
            phone="+2",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="assign_unit_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_renters", value="10"
        )
        cls.building_a = Building.objects.create(
            owner=cls.owner,
            name="AssignA",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.building_b = Building.objects.create(
            owner=cls.owner,
            name="AssignB",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        cls.other_building = Building.objects.create(
            owner=cls.other,
            name="OtherAssignB",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        cls.unit_a = Unit.objects.create(
            owner=cls.owner,
            building=cls.building_a,
            unit="A1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit_b = Unit.objects.create(
            owner=cls.owner,
            building=cls.building_b,
            unit="B1",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        cls.other_unit = Unit.objects.create(
            owner=cls.other,
            building=cls.other_building,
            unit="O1",
            unit_type="flat",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_assign_renter_to_new_unit_success(self):
        renter = Renter.objects.create(
            unit=self.unit_a,
            name="AssignRenter",
            phone="+911234567901",
            email="assign@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/assign-unit/",
            {"unit_id": self.unit_b.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renter.refresh_from_db()
        self.assertEqual(renter.unit_id, self.unit_b.id)
        self.unit_a.refresh_from_db()
        self.unit_b.refresh_from_db()
        self.assertEqual(self.unit_a.status, Unit.VacancyStatus.VACANT)
        self.assertEqual(self.unit_b.status, Unit.VacancyStatus.OCCUPIED)

    def test_assign_renter_same_unit_returns_400(self):
        renter = Renter.objects.create(
            unit=self.unit_a,
            name="SameUnitRenter",
            phone="+911234567902",
            email="same@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/assign-unit/",
            {"unit_id": self.unit_a.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assign_renter_to_other_user_unit_returns_404(self):
        renter = Renter.objects.create(
            unit=self.unit_a,
            name="OtherUnitRenter",
            phone="+911234567903",
            email="otherunit@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/assign-unit/",
            {"unit_id": self.other_unit.id},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_assign_renter_to_occupied_unit_returns_409(self):
        Renter.objects.create(
            unit=self.unit_b,
            name="OccupantRenter",
            phone="+911234567904",
            email="occupant@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        renter = Renter.objects.create(
            unit=self.unit_a,
            name="ConflictRenter",
            phone="+911234567905",
            email="conflict@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/assign-unit/",
            {"unit_id": self.unit_b.id},
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_assign_renter_missing_unit_id_returns_400(self):
        renter = Renter.objects.create(
            unit=self.unit_a,
            name="MissingIdRenter",
            phone="+911234567906",
            email="missingid@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/assign-unit/",
            {},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_assign_renter(self):
        renter = Renter.objects.create(
            unit=self.unit_a,
            name="CrossOwnerRenter",
            phone="+911234567907",
            email="cross@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        response = _auth(self.other).post(
            f"/properties/renters/{renter.id}/assign-unit/",
            {"unit_id": self.unit_b.id},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_assign_renter_clears_renter_cache(self):
        renter = Renter.objects.create(
            unit=self.unit_a,
            name="CacheRenter",
            phone="+911234567908",
            email="cache@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        cache.set(f"renters_user_{self.owner.id}", [renter])
        response = self._c.post(
            f"/properties/renters/{renter.id}/assign-unit/",
            {"unit_id": self.unit_b.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(cache.get(f"renters_user_{self.owner.id}"))


class RenterViewSetNoticePeriodTests(TestCase):
    """Cover notice_start_date auto-set on status change."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rv_np_owner",
            password="p",
            full_name="RvNPOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rv_np_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RvNPB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RVNP1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_update_status_to_notice_period_sets_notice_start_date(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="NoticePeriodRenter",
            phone="+911234567901",
            email="npr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.ACTIVE,
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/update-status/",
            {"status": "notice_period"},
        )
        self.assertEqual(response.status_code, 200)
        renter.refresh_from_db()
        self.assertEqual(renter.status, Renter.RenterStatus.NOTICE_PERIOD)
        self.assertIsNotNone(renter.notice_start_date)
        self.assertEqual(renter.notice_start_date, timezone.now().date())

    def test_update_status_to_active_clears_notice_start_date(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="ActiveRenter",
            phone="+911234567902",
            email="activenpr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.NOTICE_PERIOD,
            notice_start_date=timezone.now().date(),
        )
        response = self._c.post(
            f"/properties/renters/{renter.id}/update-status/",
            {"status": "active"},
        )
        self.assertEqual(response.status_code, 200)
        renter.refresh_from_db()
        self.assertEqual(renter.status, Renter.RenterStatus.ACTIVE)
        self.assertIsNone(renter.notice_start_date)

    def test_list_returns_deactivated_renters(self):
        Renter.objects.create(
            unit=self.unit,
            name="DeactivatedRenter",
            phone="+911234567903",
            email="deactr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.DEACTIVATED,
        )
        response = self._c.get("/properties/renters/")
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertIn("DeactivatedRenter", names)

    def test_list_returns_revoked_renters(self):
        Renter.objects.create(
            unit=self.unit,
            name="RevokedRenter",
            phone="+911234567904",
            email="revokedr@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status=Renter.RenterStatus.REVOKED,
        )
        response = self._c.get("/properties/renters/")
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertIn("RevokedRenter", names)


class TestRenterSearchFilterOrdering:
    """Tests for renter list search, filter, and ordering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="renter_sfo_owner",
            password="p",
            full_name="RenterSFOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="renter_sfo_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RenterSFOBuilding",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RSFOU1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        cache.clear()
        self._c = APIClient()
        token = RefreshToken.for_user(self.owner).access_token
        self._c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_search_by_name(self):
        Renter.objects.create(
            unit=self.unit,
            name="Alice Search",
            phone="+911111111111",
            email="alice@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        Renter.objects.create(
            unit=self.unit,
            name="Bob Search",
            phone="+922222222222",
            email="bob@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        response = self._c.get("/properties/renters/", {"search": "Alice"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertIn("Alice Search", names)
        self.assertNotIn("Bob Search", names)

    def test_search_by_phone(self):
        Renter.objects.create(
            unit=self.unit,
            name="PhoneRenter",
            phone="+911111111111",
            email="phone@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        response = self._c.get("/properties/renters/", {"search": "111111"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertIn("PhoneRenter", names)

    def test_search_by_email(self):
        Renter.objects.create(
            unit=self.unit,
            name="EmailRenter",
            phone="+911111111112",
            email="email_search@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        response = self._c.get("/properties/renters/", {"search": "email_search"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertIn("EmailRenter", names)

    def test_filter_by_status(self):
        Renter.objects.create(
            unit=self.unit,
            name="ActiveRenter",
            phone="+911111111111",
            email="active@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        Renter.objects.create(
            unit=self.unit,
            name="NoticeRenter",
            phone="+922222222222",
            email="notice@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="notice_period",
        )
        response = self._c.get("/properties/renters/", {"status": "active"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertIn("ActiveRenter", names)
        self.assertNotIn("NoticeRenter", names)

    def test_filter_by_building(self):
        other_owner = User.objects.create_user(
            username="renter_sfo_other",
            password="p",
            full_name="Other",
            phone="+2",
        )
        other_building = Building.objects.create(
            owner=other_owner,
            name="OtherBuilding",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        other_unit = Unit.objects.create(
            owner=other_owner,
            building=other_building,
            unit="OB1",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        Renter.objects.create(
            unit=self.unit,
            name="TargetRenter",
            phone="+911111111111",
            email="target@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        Renter.objects.create(
            unit=other_unit,
            name="OtherRenter",
            phone="+922222222222",
            email="other@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        response = self._c.get(
            "/properties/renters/", {"building": str(self.building.id)}
        )
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertIn("TargetRenter", names)
        self.assertNotIn("OtherRenter", names)

    def test_ordering_by_name(self):
        Renter.objects.create(
            unit=self.unit,
            name="Zebra",
            phone="+911111111111",
            email="z@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        Renter.objects.create(
            unit=self.unit,
            name="Alpha",
            phone="+922222222222",
            email="a@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        response = self._c.get("/properties/renters/", {"ordering": "name"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertEqual(names[0], "Alpha")
        self.assertEqual(names[1], "Zebra")

    def test_ordering_by_rent_amount(self):
        Renter.objects.create(
            unit=self.unit,
            name="LowRent",
            phone="+911111111111",
            email="low@test.com",
            rent_amount=Decimal("5000"),
            start_date=timezone.now().date(),
            status="active",
        )
        Renter.objects.create(
            unit=self.unit,
            name="HighRent",
            phone="+922222222222",
            email="high@test.com",
            rent_amount=Decimal("15000"),
            start_date=timezone.now().date(),
            status="active",
        )
        response = self._c.get("/properties/renters/", {"ordering": "rent_amount"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertEqual(names[0], "LowRent")
        self.assertEqual(names[1], "HighRent")

    def test_cross_owner_isolation(self):
        other_owner = User.objects.create_user(
            username="renter_sfo_other2",
            password="p",
            full_name="Other2",
            phone="+3",
        )
        other_building = Building.objects.create(
            owner=other_owner,
            name="OtherBuilding2",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        other_unit = Unit.objects.create(
            owner=other_owner,
            building=other_building,
            unit="OB2",
            unit_type="flat",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        Renter.objects.create(
            unit=other_unit,
            name="OtherOwnerRenter",
            phone="+933333333333",
            email="other2@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
            status="active",
        )
        response = self._c.get("/properties/renters/", {"search": "OtherOwnerRenter"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
