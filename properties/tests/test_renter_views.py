"""Comprehensive pytest tests for properties/views/renter_views.py."""

from decimal import Decimal
from unittest.mock import patch

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
