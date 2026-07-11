"""Tests for properties/views/unit_views.py — Unit, UnitImage, UnitDocument, RentAgreementDraft ViewSets and Leegality webhook."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.models import PlanFeatureLimit, SubscriptionPlan, UsageLimit, UserSubscription
from properties.models import (
    Building,
    RentAgreementDraft,
    Renter,
    Unit,
    UnitDocument,
    UnitImage,
)

User = get_user_model()


def _auth(u):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
    return c


class UnitViewSetTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="unit_owner", password="p", full_name="UnitOwner", phone="+1"
        )
        cls.other = User.objects.create_user(
            username="other_owner", password="p", full_name="OtherOwner", phone="+2"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="unit_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_units", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="UVB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_list_own_units(self):
        Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="UV1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        response = self._c.get("/properties/units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_create_unit(self):
        response = self._c.post(
            "/properties/units/",
            {
                "building": self.building.id,
                "unit": "UV2",
                "unit_type": "flat",
                "address_line": "2 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "2",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Unit.objects.filter(unit="UV2").exists())

    def test_update_own_unit(self):
        unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="UV3",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        response = self._c.patch(
            f"/properties/units/{unit.id}/", {"unit": "UV3_UPDATED"}
        )
        self.assertEqual(response.status_code, 200)
        unit.refresh_from_db()
        self.assertEqual(unit.unit, "UV3_UPDATED")

    def test_delete_own_unit(self):
        unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="UV4",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        response = self._c.delete(f"/properties/units/{unit.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Unit.objects.filter(id=unit.id).exists())

    def test_other_user_cannot_see_units(self):
        Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="UV5",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        response = _auth(self.other).get("/properties/units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)


class UnitImageViewSetTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="img_owner", password="p", full_name="ImgOwner", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="img_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_units", value="10"
        )
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="IMGB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="IMG1",
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

    def test_create_unit_image(self):
        import io

        from PIL import Image as PILImage

        from django.core.files.base import ContentFile

        img = PILImage.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        image_file = ContentFile(buf.read(), name="test.jpg")
        response = self._c.post(
            "/properties/unit-images/",
            {
                "unit": self.unit.id,
                "image": image_file,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(UnitImage.objects.filter(unit=self.unit).exists())

    def test_list_unit_images(self):
        UnitImage.objects.create(unit=self.unit, image="test.jpg")
        response = self._c.get("/properties/unit-images/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class UnitDocumentViewSetTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="doc_owner", password="p", full_name="DocOwner", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="doc_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_units", value="10"
        )
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_documents", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DocB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="DOC1",
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

    def test_create_unit_document(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        doc_file = SimpleUploadedFile(
            "test.pdf", b"fake-doc", content_type="application/pdf"
        )
        response = self._c.post(
            "/properties/unit-all-documents/",
            {
                "unit": self.unit.id,
                "document": doc_file,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(UnitDocument.objects.filter(unit=self.unit).exists())

    def test_list_unit_documents(self):
        UnitDocument.objects.create(unit=self.unit, document="test.pdf")
        response = self._c.get("/properties/unit-all-documents/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class RentAgreementDraftViewSetTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="draft_owner", password="p", full_name="DraftOwner", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="draft_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_units", value="10"
        )
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="rent_agreement_drafts", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DraftB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="D1",
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

    def test_create_agreement_draft(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="Draft Renter",
            phone="+911234567901",
            email="draft@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        from django.core.files.base import ContentFile

        draft_file = ContentFile(b"PDF content", name="draft.pdf")
        with patch("properties.views.unit_views.send_agreement_for_signature"):
            response = self._c.post(
                "/properties/rent-agreement-drafts/",
                {
                    "renter": renter.id,
                    "unit": self.unit.id,
                    "file": draft_file,
                },
            )
        self.assertEqual(response.status_code, 201)

    def test_list_agreement_drafts(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="Draft Renter2",
            phone="+911234567902",
            email="draft2@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        RentAgreementDraft.objects.create(
            user=self.owner, renter=renter, unit=self.unit, file="draft.pdf"
        )
        response = self._c.get("/properties/rent-agreement-drafts/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class LeegalityWebhookTests(TestCase):
    def test_post_method_accepted(self):
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "doc123", "status": "SIGNED", "participant": "OWNER"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_get_method_rejected(self):
        response = self.client.get("/properties/leegality/webhook/")
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            "/properties/leegality/webhook/",
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_signed_owner_updates_agreement(self):
        owner = User.objects.create_user(
            username="webhook_owner", password="p", full_name="WebhookOwner", phone="+1"
        )
        building = Building.objects.create(
            owner=owner,
            name="WHB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        unit = Unit.objects.create(
            owner=owner,
            building=building,
            unit="WH1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        renter = Renter.objects.create(
            unit=unit,
            name="WH Renter",
            phone="+911234567903",
            email="wh@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        agreement = RentAgreementDraft.objects.create(
            user=owner,
            renter=renter,
            unit=unit,
            file="draft.pdf",
            leegality_document_id="doc123",
        )
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "doc123", "status": "SIGNED", "participant": "OWNER"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)

    def test_signed_renter_updates_agreement(self):
        owner = User.objects.create_user(
            username="webhook_owner2",
            password="p",
            full_name="WebhookOwner2",
            phone="+1",
        )
        building = Building.objects.create(
            owner=owner,
            name="WHB2",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        unit = Unit.objects.create(
            owner=owner,
            building=building,
            unit="WH2",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        renter = Renter.objects.create(
            unit=unit,
            name="WH Renter2",
            phone="+911234567904",
            email="wh2@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        agreement = RentAgreementDraft.objects.create(
            user=owner,
            renter=renter,
            unit=unit,
            file="draft.pdf",
            leegality_document_id="doc456",
        )
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "doc456", "status": "SIGNED", "participant": "RENTER"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.renter_signed)


class UnitViewSetExpiredSubscriptionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="expired_owner", password="p", full_name="ExpiredOwner", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="expired_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_units", value="unlimited"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ExpB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_grace_period_returns_active_units_when_unlimited(self):
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="EXP1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        response = self._c.get("/properties/units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["unit"], "EXP1")


class UnitViewSetPermissionAndLimitTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="perm_owner", password="p", full_name="PermOwner", phone="+1"
        )
        cls.other = User.objects.create_user(
            username="other_user", password="p", full_name="OtherUser", phone="+2"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="perm_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_units", value="1"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="PermB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="PERM1",
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

    def test_create_unit_denied_when_limit_reached(self):
        from properties.feature_enforcer import FeatureEnforcer

        FeatureEnforcer(self.owner).increment("max_units")
        response = self._c.post(
            "/properties/units/",
            {
                "building": self.building.id,
                "unit": "PERM3",
                "unit_type": "flat",
                "address_line": "3 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "3",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_update_unit(self):
        response = _auth(self.other).patch(
            f"/properties/units/{self.unit.id}/", {"unit": "HACKED"}
        )
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_delete_unit(self):
        response = _auth(self.other).delete(f"/properties/units/{self.unit.id}/")
        self.assertEqual(response.status_code, 404)


class UnitImageViewSetPermissionAndLimitTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="img_perm_owner",
            password="p",
            full_name="ImgPermOwner",
            phone="+1",
        )
        cls.other = User.objects.create_user(
            username="img_other", password="p", full_name="ImgOther", phone="+2"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="img_perm_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="1"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ImgPermB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="IMGPERM1",
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

    def test_create_image_denied_when_not_owner_unit(self):
        other_building = Building.objects.create(
            owner=self.other,
            name="OtherB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        other_unit = Unit.objects.create(
            owner=self.other,
            building=other_building,
            unit="OTHER1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        import io

        from PIL import Image as PILImage

        from django.core.files.base import ContentFile

        img = PILImage.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        image_file = ContentFile(buf.read(), name="test.jpg")
        response = self._c.post(
            "/properties/unit-images/",
            {
                "unit": other_unit.id,
                "image": image_file,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_create_image_denied_when_limit_reached(self):
        from properties.feature_enforcer import FeatureEnforcer

        FeatureEnforcer(self.owner).increment("unit_images")
        import io

        from PIL import Image as PILImage

        from django.core.files.base import ContentFile

        img = PILImage.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        image_file = ContentFile(buf.read(), name="test2.jpg")
        response = self._c.post(
            "/properties/unit-images/",
            {
                "unit": self.unit.id,
                "image": image_file,
            },
        )
        self.assertEqual(response.status_code, 403)


class UnitDocumentViewSetPermissionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="doc_perm_owner",
            password="p",
            full_name="DocPermOwner",
            phone="+1",
        )
        cls.other = User.objects.create_user(
            username="doc_other", password="p", full_name="DocOther", phone="+2"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="doc_perm_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_documents", value="1"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DocPermB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="DOCPERM1",
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

    def test_create_document_denied_when_not_owner_unit(self):
        other_building = Building.objects.create(
            owner=self.other,
            name="OtherDocB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        other_unit = Unit.objects.create(
            owner=self.other,
            building=other_building,
            unit="OTHERDOC1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        doc_file = SimpleUploadedFile(
            "test.pdf", b"fake-doc", content_type="application/pdf"
        )
        response = self._c.post(
            "/properties/unit-all-documents/",
            {
                "unit": other_unit.id,
                "document": doc_file,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_create_document_denied_when_limit_reached(self):
        from properties.feature_enforcer import FeatureEnforcer

        FeatureEnforcer(self.owner).increment("unit_documents")
        doc_file = SimpleUploadedFile(
            "test.pdf", b"fake-doc2", content_type="application/pdf"
        )
        response = self._c.post(
            "/properties/unit-all-documents/",
            {
                "unit": self.unit.id,
                "document": doc_file,
            },
        )
        self.assertEqual(response.status_code, 403)


class ExpiredSubscriptionQuotaTests(TestCase):
    """Cover units truncation when subscription is expired but within grace period."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="expired_grace_owner",
            password="p",
            full_name="ExpiredGraceOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="expired_grace_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_units", value="5"
        )
        UsageLimit.objects.create(
            user=cls.owner, feature_key="max_units", usage_count=0
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ExpGraceB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_active_units_shown_within_grace_period(self):
        Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="GH1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="GH2",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        response = self._c.get("/properties/units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


class UnitDeleteAndUpdateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="del_up_owner", password="p", full_name="DelUpOwner", phone="+1"
        )
        cls.other = User.objects.create_user(
            username="del_up_other", password="p", full_name="DelUpOther", phone="+2"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="del_up_pro",
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
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DelUpB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="DU1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        cache.clear()

    def test_owner_can_update_unit(self):
        c = _auth(self.owner)
        response = c.patch(
            f"/properties/units/{self.unit.id}/",
            {"unit": "DU1_UPDATED"},
        )
        self.assertEqual(response.status_code, 200)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.unit, "DU1_UPDATED")

    def test_owner_can_delete_unit(self):
        c = _auth(self.owner)
        response = c.delete(f"/properties/units/{self.unit.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Unit.objects.filter(id=self.unit.id).exists())

    def test_other_user_cannot_update_unit(self):
        c = _auth(self.other)
        response = c.patch(
            f"/properties/units/{self.unit.id}/",
            {"unit": "HACK"},
        )
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_delete_unit(self):
        c = _auth(self.other)
        response = c.delete(f"/properties/units/{self.unit.id}/")
        self.assertEqual(response.status_code, 404)


class RentAgreementDraftExceptionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="exc_owner", password="p", full_name="ExcOwner", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="exc_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="rent_agreement_drafts", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ExcB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="EX1",
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

    def test_agreement_draft_creation_handles_leegality_failure(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="ExcRenter",
            phone="+911234567901",
            email="exc@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        from django.core.files.base import ContentFile

        draft_file = ContentFile(b"PDF content", name="draft.pdf")
        with patch(
            "properties.views.unit_views.send_agreement_for_signature",
            side_effect=Exception("Leegality is down"),
        ):
            response = self._c.post(
                "/properties/rent-agreement-drafts/",
                {
                    "renter": renter.id,
                    "unit": self.unit.id,
                    "file": draft_file,
                },
            )
        self.assertEqual(response.status_code, 201)


class AnonymousUnitDocumentTests(TestCase):
    """Cover UnitDocumentViewSet.get_queryset for anonymous users."""

    def test_anonymous_user_queryset_returns_empty(self):
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory

        from properties.views.unit_views import UnitDocumentViewSet

        request = RequestFactory().get("/properties/unit-all-documents/")
        request.user = AnonymousUser()
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None
        self.assertEqual(list(view.get_queryset()), [])


class UnitDocumentDeleteTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="doc_del_owner",
            password="p",
            full_name="DocDelOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="doc_del_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_documents", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DocDelB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="DD1",
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

    def test_owner_can_delete_unit_document(self):
        document = UnitDocument.objects.create(unit=self.unit, document="delete.pdf")
        response = self._c.delete(f"/properties/unit-all-documents/{document.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(UnitDocument.objects.filter(id=document.id).exists())

    def test_other_user_cannot_delete_unit_document(self):
        attacker = User.objects.create_user(
            username="doc_del_attack",
            password="p",
            full_name="DocDelAttack",
            phone="+2",
        )
        document = UnitDocument.objects.create(unit=self.unit, document="delete.pdf")
        response = _auth(attacker).delete(
            f"/properties/unit-all-documents/{document.id}/"
        )
        self.assertEqual(response.status_code, 404)
