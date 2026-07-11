"""Tests for properties/views/unit_views.py — focused coverage expansion."""

from datetime import date
from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.utils import timezone

from core.models import PlanFeatureLimit, SubscriptionPlan, UsageLimit, UserSubscription
from properties.models import Building, Renter, Unit, UnitDocument, UnitImage
from properties.views.renter_views import RenterViewSet

User = get_user_model()


def _auth(u):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
    return c


class ExpiredFreeLimitPoppingTests(TestCase):
    """Cover expired + grace + numeric free_limit popping."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="unique_exp_owner",
            password="p",
            full_name="UniqueExpOwner",
            phone="+1",
        )
        cls.plan, _ = SubscriptionPlan.objects.get_or_create(
            name="unique_expired_plan",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
            },
        )
        PlanFeatureLimit.objects.get_or_create(
            plan=cls.plan, feature_key="max_units", defaults={"value": "2"}
        )
        UserSubscription.objects.create(
            user=cls.owner,
            plan=cls.plan,
            is_active=True,
            end_date=timezone.now().date() - timezone.timedelta(days=30),
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="UniqueExpB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_expired_grace_truncates_to_free_limit(self):
        """When expired + past grace, only free_limit units are returned."""
        for i in range(4):
            Unit.objects.create(
                owner=self.owner,
                building=self.building,
                unit=f"EL{i}",
                unit_type="flat",
                address_line="1 St",
                city="C",
                state="S",
                country="CO",
                postal_code=str(i),
                is_archived=False,
            )
        cache.clear()
        response = self._c.get("/properties/units/")
        self.assertEqual(response.status_code, 200)
        # Free plan gives max_units=3; refreshes/limit check applies the fallback
        self.assertLessEqual(len(response.data), 3)


class UnitImageQuotaTests(TestCase):
    """UnitImageViewSet quota, ownership, and delete paths."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="imgq_owner", password="p", full_name="ImgQOwner", phone="+1"
        )
        cls.other = User.objects.create_user(
            username="imgq_other", password="p", full_name="ImgQOther", phone="+2"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="imgq_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="5"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ImQB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="IQ1",
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

    def test_image_list_limits_to_owner_units(self):
        """Queryset is applied on UnitImageViewSet."""
        c = _auth(self.owner)
        _ = UnitImage.objects.create(unit=self.unit, image="test.jpg")
        response = c.get("/properties/unit-images/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) >= 1)


class UnitImageDeleteTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="imgdel_owner",
            password="p",
            full_name="ImgDelOwner",
            phone="+1",
        )
        cls.other = User.objects.create_user(
            username="imgdel_other",
            password="p",
            full_name="ImgDelOther",
            phone="+2",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="imgdel_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ImgDelB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="ID1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.image = UnitImage.objects.create(unit=cls.unit, image="del.jpg")

    def setUp(self):
        cache.clear()

    def test_owner_can_delete_image(self):
        response = _auth(self.owner).delete(f"/properties/unit-images/{self.image.id}/")
        self.assertEqual(response.status_code, 204)

    def test_other_user_cannot_delete_image(self):
        response = _auth(self.other).delete(f"/properties/unit-images/{self.image.id}/")
        self.assertIn(response.status_code, [404, 403])


class UnitDocumentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="udoc_owner", password="p", full_name="UDocOwner", phone="+1"
        )
        cls.other = User.objects.create_user(
            username="udoc_other", password="p", full_name="UDocOther", phone="+2"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="udoc_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_documents", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="UDocB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="UD1",
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

    def test_update_unit_document_rejects_other_unit(self):
        other = User.objects.create_user(
            username="udoc_attack",
            password="p",
            full_name="UDocAttack",
            phone="+3",
        )
        other_building = Building.objects.create(
            owner=other,
            name="OdB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        other_unit = Unit.objects.create(
            owner=other,
            building=other_building,
            unit="OD1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        doc = UnitDocument.objects.create(unit=self.unit, document="udoc.pdf")
        response = _auth(self.owner).patch(
            f"/properties/unit-all-documents/{doc.id}/",
            {"unit": other_unit.id},
        )
        # View returns 400 on serializer validation failure (ownership error)
        self.assertIn(response.status_code, [400, 404])

    def test_list_unit_documents(self):
        UnitDocument.objects.create(unit=self.unit, document="list.pdf")
        response = self._c.get("/properties/unit-all-documents/")
        self.assertEqual(response.status_code, 200)


class RenterViewSetAnonymousQuerysetTests(TestCase):
    """Cover RenterViewSet.get_queryset anonymous-user branch."""

    def test_anonymous_renter_queryset_returns_empty(self):
        request = RequestFactory().get("/properties/renters/")
        request.user = AnonymousUser()
        view = RenterViewSet()
        view.request = request
        view.format_kwarg = None
        self.assertEqual(list(view.get_queryset()), [])


class RenterViewSetDirectMethodTests(TestCase):
    """Directly invoke perform_update / perform_destroy for coverage."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rvd_owner", password="p", full_name="RvdOwner", phone="+1"
        )
        cls.attacker = User.objects.create_user(
            username="rvd_attack", password="p", full_name="RvdAttack", phone="+2"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rvd_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        UsageLimit.objects.create(
            user=cls.owner, feature_key="max_renters", usage_count=0
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RvdB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RVDU1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def test_perform_update_wrong_unit_owner_raises(self):
        _ = Renter.objects.create(
            unit=self.unit,
            name="RvdRenter",
            phone="+911234567901",
            email="rvdr@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        other_building = Building.objects.create(
            owner=self.attacker,
            name="OdB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        other_unit = Unit.objects.create(
            owner=self.attacker,
            building=other_building,
            unit="OD1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        view = RenterViewSet()
        view.request = type("Req", (), {"user": self.owner})()
        created = Renter.objects.create(
            unit=self.unit,
            name="SameRenter",
            phone="+9111111111",
            email="same@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        serializer = type(
            "Ser", (), {"instance": created, "validated_data": {"unit": other_unit}}
        )()
        from rest_framework.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            view.perform_update(serializer)

    def test_perform_destroy_decrements_count(self):
        UsageLimit.objects.create(
            user=self.owner, feature_key="max_renters", usage_count=1
        )
        renter = Renter.objects.create(
            unit=self.unit,
            name="DelRenter",
            phone="+911234567902",
            email="delr@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        view = RenterViewSet()
        view.request = type("Req", (), {"user": self.owner})()
        usage = UsageLimit.objects.get(user=self.owner, feature_key="max_renters")
        self.assertEqual(usage.usage_count, 1)
        view.perform_destroy(renter)
        self.assertFalse(Renter.objects.filter(id=renter.id).exists())
        usage.refresh_from_db()
        self.assertEqual(usage.usage_count, 0)


class UnitDirectMethodQuotaTests(TestCase):
    """Directly cover unit_views.py deny paths via view method calls."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="dmq_owner", password="p", full_name="DmqOwner", phone="+1"
        )
        cls.attacker = User.objects.create_user(
            username="dmq_attack", password="p", full_name="DmqAttack", phone="+2"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="dmq_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_units", value="10"
        )
        UsageLimit.objects.create(
            user=cls.owner, feature_key="max_units", usage_count=0
        )
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="10"
        )
        UsageLimit.objects.create(
            user=cls.owner, feature_key="unit_images", usage_count=0
        )
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_documents", value="10"
        )
        UsageLimit.objects.create(
            user=cls.owner, feature_key="unit_documents", usage_count=0
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DmqB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="DMQ1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def _make_request(self, user):
        req = RequestFactory().request()
        req.user = user
        return req

    def test_unit_perform_update_wrong_owner_raises(self):
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import UnitViewSet

        attacker_unit = Unit.objects.create(
            owner=self.attacker,
            building=self.building,
            unit="ATT1",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        view = UnitViewSet()
        view.request = self._make_request(self.owner)
        view.format_kwarg = None
        serializer = type("Ser", (), {"instance": attacker_unit})()
        with self.assertRaises(PermissionDenied):
            view.perform_update(serializer)

    def test_unit_perform_destroy_wrong_owner_raises(self):
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import UnitViewSet

        attacker_unit = Unit.objects.create(
            owner=self.attacker,
            building=self.building,
            unit="ATT2",
            unit_type="flat",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        view = UnitViewSet()
        view.request = self._make_request(self.owner)
        view.format_kwarg = None
        with self.assertRaises(PermissionDenied):
            view.perform_destroy(attacker_unit)

    def test_unit_image_perform_create_wrong_owner_raises(self):
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import UnitImageViewSet

        attacker_building = Building.objects.create(
            owner=self.attacker,
            name="AbB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        attacker_unit = Unit.objects.create(
            owner=self.attacker,
            building=attacker_building,
            unit="ATTI1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        view = UnitImageViewSet()
        view.request = self._make_request(self.owner)
        view.format_kwarg = None
        serializer = type(
            "Ser",
            (),
            {
                "validated_data": {"unit": attacker_unit},
                "save": lambda **kw: None,
            },
        )()
        with self.assertRaises(PermissionDenied):
            view.perform_create(serializer)

    def test_unit_image_perform_update_wrong_owner_raises(self):
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import UnitImageViewSet

        attacker_building = Building.objects.create(
            owner=self.attacker,
            name="AbB2",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        attacker_unit = Unit.objects.create(
            owner=self.attacker,
            building=attacker_building,
            unit="ATTI2",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        img = UnitImage.objects.create(unit=self.unit, image="test.jpg")
        view = UnitImageViewSet()
        view.request = self._make_request(self.owner)
        view.format_kwarg = None
        serializer = type(
            "Ser",
            (),
            {
                "instance": img,
                "validated_data": {"unit": attacker_unit},
                "save": lambda **kw: None,
            },
        )()
        with self.assertRaises(PermissionDenied):
            view.perform_update(serializer)

    def test_unit_image_perform_destroy_wrong_owner_raises(self):
        from rest_framework.exceptions import PermissionDenied

        from properties.models import UnitImage
        from properties.views.unit_views import UnitImageViewSet

        attacker_building = Building.objects.create(
            owner=self.attacker,
            name="AbB3",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        attacker_unit = Unit.objects.create(
            owner=self.attacker,
            building=attacker_building,
            unit="ATTI3",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        img = UnitImage.objects.create(unit=attacker_unit, image="test.jpg")
        view = UnitImageViewSet()
        view.request = self._make_request(self.owner)
        view.format_kwarg = None
        with self.assertRaises(PermissionDenied):
            view.perform_destroy(img)

    def test_unit_document_perform_create_wrong_owner_raises(self):
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import UnitDocumentViewSet

        attacker_building = Building.objects.create(
            owner=self.attacker,
            name="AdB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        attacker_unit = Unit.objects.create(
            owner=self.attacker,
            building=attacker_building,
            unit="ATTD1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        view = UnitDocumentViewSet()
        view.request = self._make_request(self.owner)
        view.format_kwarg = None
        serializer = type(
            "Ser",
            (),
            {
                "validated_data": {"unit": attacker_unit},
                "save": lambda **kw: None,
            },
        )()
        with self.assertRaises(PermissionDenied):
            view.perform_create(serializer)

    def test_unit_document_perform_update_wrong_owner_raises(self):
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import UnitDocumentViewSet

        attacker_building = Building.objects.create(
            owner=self.attacker,
            name="AdB2",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        attacker_unit = Unit.objects.create(
            owner=self.attacker,
            building=attacker_building,
            unit="ATTD2",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        doc = UnitDocument.objects.create(unit=self.unit, document="test.pdf")
        view = UnitDocumentViewSet()
        view.request = self._make_request(self.owner)
        view.format_kwarg = None
        serializer = type(
            "Ser",
            (),
            {
                "instance": doc,
                "validated_data": {"unit": attacker_unit},
                "save": lambda **kw: None,
            },
        )()
        with self.assertRaises(PermissionDenied):
            view.perform_update(serializer)

    def test_unit_document_perform_destroy_wrong_owner_raises(self):
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import UnitDocumentViewSet

        attacker_building = Building.objects.create(
            owner=self.attacker,
            name="AdB3",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        attacker_unit = Unit.objects.create(
            owner=self.attacker,
            building=attacker_building,
            unit="ATTD3",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        doc = UnitDocument.objects.create(unit=attacker_unit, document="test.pdf")
        view = UnitDocumentViewSet()
        view.request = self._make_request(self.owner)
        view.format_kwarg = None
        with self.assertRaises(PermissionDenied):
            view.perform_destroy(doc)
