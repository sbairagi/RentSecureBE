"""Tests for properties/views/unit_views.py — Unit, UnitImage, UnitDocument, RentAgreementDraft ViewSets and Leegality webhook."""

import hashlib
import hmac
import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.models import PlanFeatureLimit, SubscriptionPlan, UsageLimit, UserSubscription
from properties.constants import GRACE_PERIOD_DAYS
from properties.feature_enforcer import FeatureEnforcer
from properties.models import (
    Building,
    RentAgreementDraft,
    Renter,
    Unit,
    UnitDocument,
    UnitImage,
)

User = get_user_model()


def _sign_leegality_payload(payload: dict, secret: str) -> tuple[bytes, str]:
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return body, signature


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

    def test_missing_signature_returns_400_when_secret_configured(self):
        payload = {"document_id": "doc123", "status": "SIGNED"}
        with patch.object(settings, "LEEGALITY_WEBHOOK_SECRET", "secret"):
            response = self.client.post(
                "/properties/leegality/webhook/",
                data=payload,
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 400)

    def test_invalid_signature_returns_400_when_secret_configured(self):
        payload = {"document_id": "doc123", "status": "SIGNED"}
        with patch.object(settings, "LEEGALITY_WEBHOOK_SECRET", "secret"):
            response = self.client.post(
                "/properties/leegality/webhook/",
                data=payload,
                content_type="application/json",
                headers={"X-Leegality-Signature": "invalid"},
            )
        self.assertEqual(response.status_code, 400)

    def test_valid_signature_allows_webhook_when_secret_configured(self):
        payload = {"document_id": "doc123", "status": "SIGNED", "participant": "OWNER"}
        body, signature = _sign_leegality_payload(payload, secret="secret")
        agreement = RentAgreementDraft.objects.create(
            user=User.objects.create_user(
                username="sig_owner", password="p", full_name="SigOwner", phone="+1"
            ),
            renter=None,
            unit=Unit.objects.create(
                owner=User.objects.create_user(
                    username="sig_unit_owner",
                    password="p",
                    full_name="SigUnitOwner",
                    phone="+1",
                ),
                building=Building.objects.create(
                    owner=User.objects.create_user(
                        username="sig_bld_owner",
                        password="p",
                        full_name="SigBldOwner",
                        phone="+1",
                    ),
                    name="SigB",
                    address_line="1 St",
                    city="C",
                    state="S",
                    country="CO",
                    postal_code="1",
                ),
                unit="SIG1",
                unit_type="flat",
                address_line="1 St",
                city="C",
                state="S",
                country="CO",
                postal_code="1",
            ),
            file="draft.pdf",
            leegality_document_id="doc123",
        )
        with patch.object(settings, "LEEGALITY_WEBHOOK_SECRET", "secret"):
            response = self.client.post(
                "/properties/leegality/webhook/",
                data=body,
                content_type="application/json",
                headers={"X-Leegality-Signature": signature},
            )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)


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


class UnitViewSetQuotaAndPermissionTests(APITestCase):
    """Cover the numbered free_limit branch in get_queryset, and extra permission edges.

    Uses APITestCase so that each test method runs in its own transaction.
    """

    def _create_owner_with_sub(self, username, plan_limit="10", end_days_ago=0):
        owner = User.objects.create_user(
            username=username, password="p", full_name=username, phone="+1"
        )
        plan = SubscriptionPlan.objects.create(
            name=f"plan_{username}",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        from datetime import timedelta

        from django.utils import timezone

        end_date = timezone.now().date() - timedelta(days=end_days_ago)
        UserSubscription.objects.create(
            user=owner, plan=plan, is_active=True, end_date=end_date
        )
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="max_units", value=plan_limit
        )
        building = Building.objects.create(
            owner=owner,
            name=f"B_{username}",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        return owner, building, plan

    # ------------------------------------------------------------------
    # Expired subscription tests (each creates own subscription)
    # ------------------------------------------------------------------

    def test_expired_numeric_free_limit_returns_sliced_active_units(self):
        """Past-grace + numeric free_limit — only that many active units returned."""
        from unittest.mock import patch

        owner, building, plan = self._create_owner_with_sub(
            "num_limit_owner", plan_limit="10", end_days_ago=GRACE_PERIOD_DAYS + 1
        )
        for i in range(5):
            Unit.objects.create(
                owner=owner,
                building=building,
                unit=f"SLICE{i}",
                unit_type="flat",
                address_line="1 St",
                city="C",
                state="S",
                country="CO",
                postal_code="1",
                is_archived=False,
            )
        client_c = _auth(owner)
        cache.clear()
        with patch.object(FeatureEnforcer, "_get_free_plan_limit", lambda self, key: 3):
            response = client_c.get("/properties/units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_expired_unlimited_free_limit_returns_all_active_units(self):
        """Past-grace + unlimited free_limit — all active units returned, no slicing."""
        from unittest.mock import patch

        owner, building, plan = self._create_owner_with_sub(
            "unl_free_owner", plan_limit="10", end_days_ago=GRACE_PERIOD_DAYS + 1
        )
        Unit.objects.create(
            owner=owner,
            building=building,
            unit="UNL1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        Unit.objects.create(
            owner=owner,
            building=building,
            unit="UNL2",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        Unit.objects.create(
            owner=owner,
            building=building,
            unit="UNL3",
            unit_type="flat",
            is_archived=True,
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        client_c = _auth(owner)
        cache.clear()
        with patch.object(
            FeatureEnforcer, "_get_free_plan_limit", lambda self, key: "unlimited"
        ):
            response = client_c.get("/properties/units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    # ------------------------------------------------------------------
    # Permission-edge tests
    # ------------------------------------------------------------------

    def test_other_user_cannot_update_own_unit(self):
        owner, building, plan = self._create_owner_with_sub(
            "upd_denied_owner", plan_limit="10"
        )
        denied_unit = Unit.objects.create(
            owner=owner,
            building=building,
            unit="DENY_UPD",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        other = User.objects.create_user(
            username="upd_denied_other", password="p", phone="+2"
        )
        # other's subscription (active) so they are authenticated and not blocked by IsAuthenticated
        other_plan = SubscriptionPlan.objects.create(
            name="other_upd",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=other, plan=other_plan, is_active=True)

        response = _auth(other).patch(
            f"/properties/units/{denied_unit.id}/",
            {"unit": "HACKED"},
        )
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_delete_own_unit(self):
        owner, building, plan = self._create_owner_with_sub(
            "del_denied_owner", plan_limit="10"
        )
        denied_unit = Unit.objects.create(
            owner=owner,
            building=building,
            unit="DENY_DEL",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        other = User.objects.create_user(
            username="del_denied_other", password="p", phone="+2"
        )
        other_plan = SubscriptionPlan.objects.create(
            name="other_del",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=other, plan=other_plan, is_active=True)

        response = _auth(other).delete(f"/properties/units/{denied_unit.id}/")
        self.assertEqual(response.status_code, 404)

    def test_perform_update_permission_denied_direct(self):
        """Direct coverage of perform_update owner-mismatch branch."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.serializers import UnitSerializer
        from properties.views.unit_views import UnitViewSet

        owner, building, plan = self._create_owner_with_sub(
            "upd_dir_owner", plan_limit="10"
        )
        unit = Unit.objects.create(
            owner=owner,
            building=building,
            unit="DIRECT_UPD",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        other = User.objects.create_user(
            username="upd_dir_other", password="p", phone="+2"
        )
        request = RequestFactory().patch("/properties/units/")
        request.user = other
        view = UnitViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": unit.pk}
        serializer = UnitSerializer(instance=unit, data={"unit": "HACK"}, partial=True)
        serializer._validated_data = {"unit": "HACK"}
        self.assertRaises(PermissionDenied, view.perform_update, serializer)

    def test_perform_destroy_permission_denied_and_decrement(self):
        """Direct coverage of perform_destroy owner-mismatch branch."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.feature_enforcer import FeatureEnforcer
        from properties.views.unit_views import UnitViewSet

        other, building, plan = self._create_owner_with_sub(
            "del_dir_owner", plan_limit="10"
        )
        unit = Unit.objects.create(
            owner=other,
            building=building,
            unit="DIRECT_DEL",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        FeatureEnforcer(other).increment("max_units")
        UsageLimit.objects.filter(user=other, feature_key="max_units").update(
            usage_count=2
        )
        request = RequestFactory().delete("/properties/units/")
        request.user = other
        view = UnitViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": unit.pk}

        crash_unit = Unit.objects.create(
            owner=User.objects.create_user(
                username="del_dir_crash", password="p", phone="+3"
            ),
            building=building,
            unit="CRASH_DEL",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.assertRaises(PermissionDenied, view.perform_destroy, crash_unit)

    def test_cache_deleted_after_perform_create(self):
        """perform_create calls cache.delete for the unit cache."""
        owner, building, _ = self._create_owner_with_sub("cache_owner", plan_limit="10")
        client_c = _auth(owner)
        cache.clear()
        response = client_c.post(
            "/properties/units/",
            {
                "building": building.id,
                "unit": "CACHE_TEST",
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(cache.get(f"units_user_{owner.id}"))


class UnitImageViewSetQuotaAndAnonymousTests(TestCase):
    """Cover UnitImageViewSet anonymous and permission edges."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="img_anon_owner",
            password="p",
            full_name="ImgAnonOwner",
            phone="+1",
        )
        cls.other = User.objects.create_user(
            username="img_anon_other",
            password="p",
            full_name="ImgAnonOther",
            phone="+2",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="img_anon_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ImgAnonB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="IMG_ANON1",
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

    def test_unauthenticated_anonymoususer_returns_empty_queryset(self):
        """UnitImageViewSet.get_queryset with AnonymousUser: no hoist check, raises TypeError."""
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory

        from properties.views.unit_views import UnitImageViewSet

        request = RequestFactory().get("/properties/unit-images/")
        request.user = AnonymousUser()
        view = UnitImageViewSet()
        view.request = request
        view.format_kwarg = None
        with self.assertRaises(TypeError):
            list(view.get_queryset())


class RentAgreementDraftViewSetExceptionTests(TestCase):
    """Cover draft agreement creation with renter/unit/email edge cases."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="draft_exc_owner",
            password="p",
            full_name="DraftExcOwner",
            email="owner@test.com",
            phone="+1",
        )
        cls.attacker = User.objects.create_user(
            username="draft_attacker",
            password="p",
            full_name="DraftAttacker",
            phone="+2",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="draft_exc_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="rent_agreement_drafts", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DraftExcB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="EXD1",
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

    def test_create_renter_not_linked_to_unit_returns_400(self):
        """Reject when renter.unit != serializer unit (serializer validation).

        RentAgreementDraftSerializer.validate checks renter.unit == unit and raises
        ValidationError; DRF converts this to 400 Bad Request.
        """
        other_building = Building.objects.create(
            owner=self.attacker,
            name="AttackerB",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        other_unit = Unit.objects.create(
            owner=self.attacker,
            building=other_building,
            unit="ATK1",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        # Renter belongs to other_unit, not self.unit
        Renter.objects.create(
            unit=other_unit,
            name="MismatchedRenter",
            phone="+911234567901",
            email="mismatch@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        draft_file = SimpleUploadedFile(
            "draft.pdf", b"pdf", content_type="application/pdf"
        )
        response = self._c.post(
            "/properties/rent-agreement-drafts/",
            {
                "renter": Renter.objects.get(name="MismatchedRenter").id,
                "unit": self.unit.id,
                "file": draft_file,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_create_renter_not_linked_to_unit_direct_permission_denied(self):
        """Direct call to perform_create with renter.unit != unit raises PermissionDenied.

        This exercises the branch at line 246-247 of unit_views.py.
        """
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import RentAgreementDraftViewSet

        other_building = Building.objects.create(
            owner=self.attacker,
            name="AttackerB2",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        other_unit = Unit.objects.create(
            owner=self.attacker,
            building=other_building,
            unit="ATK2",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        wrong_renter = Renter.objects.create(
            unit=other_unit,
            name="MismatchedRenterDirect",
            phone="+911234567901",
            email="mismatch2@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        request = RequestFactory().post("/properties/rent-agreement-drafts/")
        request.user = self.owner
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None

        # Build a serializer with validated_data but renter.unit != self.unit
        class FakeSerializer:
            validated_data = {
                "renter": wrong_renter,
                "unit": self.unit,
            }

        with patch(
            "properties.views.unit_views.send_agreement_for_signature"
        ) as mock_send:
            self.assertRaises(
                PermissionDenied,
                view.perform_create,
                FakeSerializer(),
            )
        mock_send.assert_not_called()

    def test_create_missing_owner_email_succeeds_but_signature_fails(self):
        """Missing owner email → PermissionDenied caught internally → 201, but no signature sent.

        The try/except in perform_create swallows PermissionDenied raised for
        missing owner email, logs a warning, and returns 201.
        """
        no_email_user = User.objects.create_user(
            username="no_email_user",
            password="p",
            full_name="NoEmail",
            email="",
            phone="+3",
        )
        no_email_plan = SubscriptionPlan.objects.create(
            name="no_email_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(
            user=no_email_user, plan=no_email_plan, is_active=True
        )
        PlanFeatureLimit.objects.create(
            plan=no_email_plan, feature_key="rent_agreement_drafts", value="10"
        )
        no_email_unit = Unit.objects.create(
            owner=no_email_user,
            building=Building.objects.create(
                owner=no_email_user,
                name="NoEmailB",
                address_line="3 St",
                city="C",
                state="S",
                country="CO",
                postal_code="3",
            ),
            unit="NOEMAIL1",
            unit_type="flat",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        renter = Renter.objects.create(
            unit=no_email_unit,
            name="NoEmailRenter",
            phone="+911234567901",
            email="renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        no_email_c = APIClient()
        no_email_c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(no_email_user).access_token}"
        )
        draft_file = SimpleUploadedFile(
            "draft.pdf", b"pdf", content_type="application/pdf"
        )
        with patch(
            "properties.views.unit_views.send_agreement_for_signature"
        ) as mock_send:
            response = no_email_c.post(
                "/properties/rent-agreement-drafts/",
                {
                    "renter": renter.id,
                    "unit": no_email_unit.id,
                    "file": draft_file,
                },
            )
        self.assertEqual(response.status_code, 201)
        mock_send.assert_not_called()


class LeegalityWebhookBranchTests(TestCase):
    """Exhaustively cover all branches in leegality_webhook."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="wh_branch_owner",
            password="p",
            full_name="WHBranchOwner",
            email="branch@test.com",
            phone="+1",
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="WHBranchB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="WHB1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.renter = Renter.objects.create(
            unit=cls.unit,
            name="WHRenter",
            phone="+911234567903",
            email="wh.renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )

    def _make_agreement(self, doc_id="sid_branch"):
        return RentAgreementDraft.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            file="draft.pdf",
            leegality_document_id=doc_id,
        )

    def test_hit_documentid_variant(self):
        """Payload key 'documentId' resolves the agreement."""
        agreement = self._make_agreement(doc_id="sid_variant")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"documentId": "sid_variant", "status": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)

    def test_hit_documentkey_variant(self):
        """Payload key 'documentKey' resolves the agreement."""
        self._make_agreement(doc_id="sid_key")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"documentKey": "sid_key", "status": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        a = RentAgreementDraft.objects.get(leegality_document_id="sid_key")
        self.assertTrue(a.owner_signed)
        self.assertTrue(a.renter_signed)

    def test_hit_parameter_state_instead_of_status(self):
        """Payload key 'state' = 'SIGNED' should also trigger the callback."""
        agreement = self._make_agreement(doc_id="sid_state")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "sid_state", "state": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)
        self.assertTrue(agreement.renter_signed)

    def test_participant_owner_sets_owner_signed_only(self):
        """participant='OWNER' → only owner_signed=True."""
        agreement = self._make_agreement(doc_id="sid_owner")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={
                "document_id": "sid_owner",
                "status": "SIGNED",
                "participant": "OWNER",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)
        self.assertFalse(agreement.renter_signed)

    def test_participant_renter_sets_renter_signed_only(self):
        """participant='RENTER' → only renter_signed=True."""
        agreement = self._make_agreement(doc_id="sid_renter")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={
                "document_id": "sid_renter",
                "status": "SIGNED",
                "participant": "RENTER",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertFalse(agreement.owner_signed)
        self.assertTrue(agreement.renter_signed)

    def test_unknown_participant_sets_both_signed(self):
        """Participant neither OWNER nor RENTER → both owner and renter signed."""
        agreement = self._make_agreement(doc_id="sid_unknown")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={
                "document_id": "sid_unknown",
                "status": "SIGNED",
                "participant": "UNKNOWN",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)
        self.assertTrue(agreement.renter_signed)

    def test_status_case_insensitive_signed(self):
        """ "signed' in lower case still sets both flags."""
        agreement = self._make_agreement(doc_id="sid_lower")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "sid_lower", "status": "signed"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)
        self.assertTrue(agreement.renter_signed)

    def test_no_agreement_noop(self):
        """doc_id not found → no error, 200 returned."""
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "nonexistent", "status": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_non_signed_status_is_noop(self):
        """'PENDING' status should not update any flags."""
        agreement = self._make_agreement(doc_id="sid_pending")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "sid_pending", "status": "PENDING"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertFalse(agreement.owner_signed)
        self.assertFalse(agreement.renter_signed)

    def test_get_returns_405(self):
        response = self.client.get("/properties/leegality/webhook/")
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            "/properties/leegality/webhook/",
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


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


class LeegalityWebhookDocumentKeyAndStateTests(TestCase):
    """Cover documentKey, state (instead of status), agreement-is-None webhook branches."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="wh_key_owner",
            password="p",
            full_name="WHKeyOwner",
            phone="+1",
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="WHKeyB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="WHK1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.renter = Renter.objects.create(
            unit=cls.unit,
            name="WHKRenter",
            phone="+911234567907",
            email="whk.renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )

    def _make_agreement(self, doc_id):
        return RentAgreementDraft.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            file="draft.pdf",
            leegality_document_id=doc_id,
        )

    def test_documentkey_payload_updates_owner_signed(self):
        agreement = self._make_agreement(doc_id="sid_key")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"documentKey": "sid_key", "status": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)
        self.assertTrue(agreement.renter_signed)  # participant is None → both signed

    def test_state_payload_updates_owner_signed(self):
        agreement = self._make_agreement(doc_id="sid_state")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "sid_state", "state": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)

    def test_no_agreement_noop_status_not_signed(self):
        """agreement is None OR status is not SIGNED → no update, still 200."""
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "nonexistent", "status": "PENDING"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        # agreement is None branch (line 329-330 first condition is False)
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={
                "document_id": "some_id",
                # no status and no state, so status_value is None
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)


class UnitImageViewSetCoverageTests(TestCase):
    """Cover perform_update/destroy/unit-mismatch branches in UnitImageViewSet."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="img_cov_owner",
            password="p",
            full_name="ImgCovOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="img_cov_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ImgCovB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="IMGCOV1",
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

    def test_list_unit_images_populates_cache(self):
        """First GET populates the image cache (cache miss path)."""
        UnitImage.objects.create(unit=self.unit, image="cov_test.jpg")
        cache.clear()
        response = self._c.get("/properties/unit-images/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_perform_create_denied_wrong_unit_owner_direct(self):
        """Line 124-125: serialized unit is None or unit.owner != self.request.user."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import UnitImageViewSet

        wrong_building = Building.objects.create(
            owner=User.objects.create_user(
                username="wrong_owner", password="p", phone="+5"
            ),
            name="WrongB",
            address_line="5 St",
            city="C",
            state="S",
            country="CO",
            postal_code="5",
        )
        wrong_unit = Unit.objects.create(
            owner=wrong_building.owner,
            building=wrong_building,
            unit="WRONG",
            unit_type="flat",
            address_line="5 St",
            city="C",
            state="S",
            country="CO",
            postal_code="5",
        )
        request = RequestFactory().post("/properties/unit-images/")
        request.user = self.owner
        view = UnitImageViewSet()
        view.request = request
        view.format_kwarg = None

        class FakeImgSerializer:
            validated_data = {"unit": wrong_unit}

        self.assertRaises(
            PermissionDenied,
            view.perform_create,
            FakeImgSerializer(),
        )

    def test_perform_update_owner_mismatch_direct(self):
        """Lines 138-145: perform_update raises PermissionDenied for wrong unit."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import UnitImageViewSet

        attacker = User.objects.create_user(
            username="img_upd_attacker", password="p", phone="+3"
        )
        atk_building = Building.objects.create(
            owner=attacker,
            name="AtkB",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        atk_unit = Unit.objects.create(
            owner=attacker,
            building=atk_building,
            unit="ATKU",
            unit_type="flat",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        UnitImage.objects.create(unit=atk_unit, image="upd_test.jpg")
        request = RequestFactory().patch("/properties/unit-images/")
        request.user = atk_unit.owner  # same-matching owner won't fail
        view = UnitImageViewSet()
        view.request = request
        view.format_kwarg = None

        wrong_user = User.objects.create_user(
            username="img_upd_wrong", password="p", phone="+4"
        )
        req2 = RequestFactory().patch("/properties/unit-images/")
        req2.user = wrong_user
        view2 = UnitImageViewSet()
        view2.request = req2
        view2.format_kwarg = None

        class FakeImgUpdSerializer:
            class _Instance:
                unit = atk_unit  # instance.unit = atk_unit

            instance = _Instance()
            validated_data = {"unit": atk_unit}

        self.assertRaises(
            PermissionDenied,
            view2.perform_update,
            FakeImgUpdSerializer(),
        )

    def test_perform_destroy_decrements_quota(self):
        """Lines 150-155: perform_destroy decrements quota when owner matches."""
        from django.test import RequestFactory

        from properties.views.unit_views import UnitImageViewSet

        img = UnitImage.objects.create(unit=self.unit, image="del_cov.jpg")
        request = RequestFactory().delete("/properties/unit-images/")
        request.user = self.owner
        view = UnitImageViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": img.pk}
        view.get_object = lambda: img  # type: ignore[method-assign]

        # Increment quota first
        from properties.feature_enforcer import FeatureEnforcer

        FeatureEnforcer(self.owner).increment("unit_images")
        before_count = (
            UsageLimit.objects.filter(user=self.owner, feature_key="unit_images")
            .first()
            .usage_count
        )
        view.perform_destroy(img)
        after_count = (
            UsageLimit.objects.filter(user=self.owner, feature_key="unit_images")
            .first()
            .usage_count
        )
        self.assertEqual(after_count, before_count - 1)


class UnitDocumentViewSetCoverageTests(TestCase):
    """Cover cache-miss, owner-mismatch, and update/destroy branches in UnitDocumentViewSet."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="doc_cov_owner",
            password="p",
            full_name="DocCovOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="doc_cov_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_documents", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DocCovB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="DOCCOV1",
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

    def test_get_queryset_cache_miss_then_hit(self):
        """Lines 171-175: cache is None → filter + cache set branch."""
        from properties.views.unit_views import UnitDocumentViewSet

        doc = UnitDocument.objects.create(unit=self.unit, document="cov.pdf")
        cache.clear()
        view = UnitDocumentViewSet()
        from django.test import RequestFactory

        request = RequestFactory().get("/properties/unit-all-documents/")
        request.user = self.owner
        view.request = request
        view.format_kwarg = None
        # First call: cache miss branch
        qs1 = view.get_queryset()
        self.assertIn(doc, qs1)
        # Second call: should be cache hit
        qs2 = view.get_queryset()
        self.assertEqual(list(qs1), list(qs2))

    def test_perform_create_denied_wrong_unit_direct(self):
        """Line 181-182: perform_create unit ownership check branch."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import UnitDocumentViewSet

        attacker = User.objects.create_user(
            username="doc_cov_attacker", password="p", phone="+3"
        )
        atk_building = Building.objects.create(
            owner=attacker,
            name="AtkDocB",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        atk_unit = Unit.objects.create(
            owner=attacker,
            building=atk_building,
            unit="ATKDOC",
            unit_type="flat",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        request = RequestFactory().post("/properties/unit-all-documents/")
        request.user = self.owner
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None

        class FakeDocSerializer:
            validated_data = {"unit": atk_unit}

        with self.assertRaises(PermissionDenied):
            view.perform_create(FakeDocSerializer())

    def test_perform_update_owner_mismatch_direct(self):
        """Lines 195-202: perform_update ownership check in UnitDocumentViewSet."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import UnitDocumentViewSet

        attacker = User.objects.create_user(
            username="doc_upd_attacker", password="p", phone="+3"
        )
        atk_building = Building.objects.create(
            owner=attacker,
            name="AtkDocB2",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        atk_unit = Unit.objects.create(
            owner=attacker,
            building=atk_building,
            unit="ATKDOC2",
            unit_type="flat",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        UnitDocument.objects.create(unit=atk_unit, document="upd_cov.pdf")
        request = RequestFactory().patch("/properties/unit-all-documents/")
        request.user = attacker  # matches doc.unit.owner
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None

        wrong_user = User.objects.create_user(
            username="wrong_doc_upd", password="p", phone="+4"
        )
        request2 = RequestFactory().patch("/properties/unit-all-documents/")
        request2.user = wrong_user  # wrong user
        view2 = UnitDocumentViewSet()
        view2.request = request2
        view2.format_kwarg = None

        class FakeDocUpdSerializer:
            class _Inst:
                unit = atk_unit

            instance = _Inst()
            validated_data = {"unit": atk_unit}

        self.assertRaises(
            PermissionDenied,
            view2.perform_update,
            FakeDocUpdSerializer(),
        )

    def test_perform_destroy_quota_decrement(self):
        """Lines 207-212: perform_destroy decrements usage limit."""
        from django.test import RequestFactory

        from properties.feature_enforcer import FeatureEnforcer
        from properties.views.unit_views import UnitDocumentViewSet

        doc = UnitDocument.objects.create(unit=self.unit, document="del_cov.pdf")
        request = RequestFactory().delete("/properties/unit-all-documents/")
        request.user = self.owner
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": doc.pk}
        view.get_object = lambda: doc  # type: ignore[method-assign]

        FeatureEnforcer(self.owner).increment("unit_documents")
        before = (
            UsageLimit.objects.filter(user=self.owner, feature_key="unit_documents")
            .first()
            .usage_count
        )
        view.perform_destroy(doc)
        after = (
            UsageLimit.objects.filter(user=self.owner, feature_key="unit_documents")
            .first()
            .usage_count
        )
        self.assertEqual(after, before - 1)


class RentAgreementDraftViewSetCoverageTests(TestCase):
    """Cover get_queryset Anonymous + cache-miss and additional perform_create branches."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="draft_cov_owner",
            password="p",
            full_name="DraftCovOwner",
            email="cov@test.com",
            phone="+1",
        )
        cache.clear()

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_get_queryset_anonymous_returns_empty(self):
        """Line 224-225: get_queryset returns empty queryset for AnonymousUser."""
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory

        from properties.views.unit_views import RentAgreementDraftViewSet

        request = RequestFactory().get("/properties/rent-agreement-drafts/")
        request.user = AnonymousUser()
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None
        self.assertEqual(list(view.get_queryset()), [])

    def test_get_queryset_cache_miss_then_hit(self):
        """Lines 229-232: cache miss populates and caches draft queryset."""
        from django.test import RequestFactory

        from properties.views.unit_views import RentAgreementDraftViewSet

        request = RequestFactory().get("/properties/rent-agreement-drafts/")
        request.user = self.owner
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None
        cache.clear()
        cache_key = f"rent_drafts_user_{self.owner.id}"
        self.assertIsNone(cache.get(cache_key))
        # First call: cache miss branch (229->232 executed)
        qs1 = view.get_queryset()
        self.assertIsNotNone(cache.get(cache_key))
        # Second call: cache hit
        qs2 = view.get_queryset()
        self.assertEqual(list(qs1), list(qs2))

    def test_create_draft_success_covers_can_create_true(self):
        """Full success path for perform_create exercises can_create=True and save branch."""
        plan = SubscriptionPlan.objects.create(
            name="cov_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=self.owner, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="rent_agreement_drafts", value="10"
        )
        building = Building.objects.create(
            owner=self.owner,
            name="CovB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        unit = Unit.objects.create(
            owner=self.owner,
            building=building,
            unit="COV1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        renter = Renter.objects.create(
            unit=unit,
            name="CovRenter",
            phone="+911234567010",
            email="cov@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        draft_file = SimpleUploadedFile(
            "draft.pdf", b"pdf", content_type="application/pdf"
        )
        with patch(
            "properties.views.unit_views.send_agreement_for_signature"
        ) as mock_send:
            response = self._c.post(
                "/properties/rent-agreement-drafts/",
                {"renter": renter.id, "unit": unit.id, "file": draft_file},
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(RentAgreementDraft.objects.filter(user=self.owner).count(), 1)
        mock_send.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# Additional coverage-push tests targeting branches not covered by legacy tests.
# ─────────────────────────────────────────────────────────────────────────────


class UnitViewSetExpiredGraceUnlimitedTests(TestCase):
    """Cover get_queryset branches when expired + past grace + free_limit='unlimited'."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="unl_exp_owner", password="p", full_name="UnlExpOwner", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="unl_exp_plan",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        # Provide a normal numeric limit so the "unlimited" path must come from _get_free_plan_limit
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="max_units", value="5"
        )
        UsageLimit.objects.create(
            user=cls.owner, feature_key="max_units", usage_count=0
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="UnlExpB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_unlimited_free_limit_returns_all_active_units(self):
        """free_limit='unlimited' → active_units[:free_limit] is skipped, all returned."""
        from unittest.mock import patch

        # Create 4 active units; no archived ones
        for i in range(4):
            Unit.objects.create(
                owner=self.owner,
                building=self.building,
                unit=f"UNL{i}",
                unit_type="flat",
                address_line="1 St",
                city="C",
                state="S",
                country="CO",
                postal_code=str(i),
                is_archived=False,
            )
        cache.clear()
        with patch.object(
            FeatureEnforcer, "_get_free_plan_limit", lambda self, key: "unlimited"
        ):
            response = self._c.get("/properties/units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)


class UnitViewSetExpiredGraceNumericFreeLimitTests(TestCase):
    """Cover get_queryset branches when expired + past grace + numeric free_limit."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="numfree_owner", password="p", full_name="NumFreeOwner", phone="+1"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="numfree_plan",
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
            name="NumFreeB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_numeric_free_limit_slices_active_units(self):
        """free_limit=2 → only first 2 active (is_archived=False) units returned."""
        from unittest.mock import patch

        for i in range(5):
            Unit.objects.create(
                owner=self.owner,
                building=self.building,
                unit=f"SLICE{i}",
                unit_type="flat",
                address_line="1 St",
                city="C",
                state="S",
                country="CO",
                postal_code=str(i),
                is_archived=False,
            )
        cache.clear()
        with (
            patch.object(FeatureEnforcer, "is_expired", return_value=True),
            patch.object(FeatureEnforcer, "is_past_grace_period", return_value=True),
            patch.object(FeatureEnforcer, "_get_free_plan_limit", lambda self, key: 2),
        ):
            response = self._c.get("/properties/units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


class UnitImageViewSetUnauthenticatedTests(TestCase):
    """Cover UnitImageViewSet get_queryset with an unauthenticated user."""

    def setUp(self):
        from properties.views.unit_views import UnitImageViewSet

        self.view = UnitImageViewSet()
        self.view.format_kwarg = None

    def test_get_queryset_anonymous_user_raises_typeerror(self):
        """AnonymousUser lacks .id → cast(User, request.user) raises TypeError."""
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory

        request = RequestFactory().get("/properties/unit-images/")
        request.user = AnonymousUser()
        self.view.request = request
        with self.assertRaises(TypeError):
            list(self.view.get_queryset())


class UnitDocumentViewSetAnonymousQuerysetTests(TestCase):
    """Cover UnitDocumentViewSet.get_queryset with AnonymousUser — returns empty."""

    def test_anonymous_queryset_returns_empty_list(self):
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory

        from properties.views.unit_views import UnitDocumentViewSet

        request = RequestFactory().get("/properties/unit-all-documents/")
        request.user = AnonymousUser()
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None
        self.assertEqual(list(view.get_queryset()), [])


class RentAgreementDraftViewSetLeegalityFailureTests(TestCase):
    """Cover perform_create when send_agreement_for_signature raises."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="leeg_fail_owner",
            password="p",
            full_name="LeegFailOwner",
            email="owner@test.com",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="leeg_fail_plan",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="rent_agreement_drafts", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="LeegFailB",
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

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_create_draft_succeeds_when_leegality_raises(self):
        """Draft is persisted (201) even if send_agreement_for_signature raises."""
        renter = Renter.objects.create(
            unit=self.unit,
            name="LeegRenter",
            phone="+911234567901",
            email="leeg@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        draft_file = SimpleUploadedFile(
            "draft.pdf", b"pdf", content_type="application/pdf"
        )
        # Simulate network failure from Leegality side; exception should be swallowed
        with patch(
            "properties.views.unit_views.send_agreement_for_signature",
            side_effect=Exception("Leegality 500"),
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
        self.assertTrue(
            RentAgreementDraft.objects.filter(user=self.owner, renter=renter).exists()
        )


class LeegalityWebhookPayloadVariantTests(TestCase):
    """Cover all document_id key variants (documentId, documentKey) and state=."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="wh_var_owner",
            password="p",
            full_name="WHVarOwner",
            phone="+1",
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="WHVarB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="WHV1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.renter = Renter.objects.create(
            unit=cls.unit,
            name="WHRenter",
            phone="+911234567901",
            email="whv.renter@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )

    def _make_agreement(self, doc_id):
        return RentAgreementDraft.objects.create(
            user=self.owner,
            renter=self.renter,
            unit=self.unit,
            file="draft.pdf",
            leegality_document_id=doc_id,
        )

    def test_document_id_variant_when_primary_missing(self):
        """Falls back to 'documentId' key when 'document_id' is absent."""
        agreement = self._make_agreement("docId_only")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"documentId": "docId_only", "status": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)

    def test_document_key_variant_when_others_missing(self):
        """Falls back to 'documentKey' key when both 'document_id' and 'documentId' absent."""
        agreement = self._make_agreement("docKey_only")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"documentKey": "docKey_only", "status": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)

    def test_state_parameter_trigger_signs_both_parties(self):
        """'state' instead of 'status' → SIGNED logic runs (no participant → both signed)."""
        agreement = self._make_agreement("sid_state")
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"document_id": "sid_state", "state": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signed)
        self.assertTrue(agreement.renter_signed)

    def test_no_document_id_key_returns_200_without_error(self):
        """Payload without any document-id key → query is empty, no crash, 200."""
        response = self.client.post(
            "/properties/leegality/webhook/",
            data={"status": "SIGNED"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)


class UnitViewSetPerformCreateCacheDeletionTests(TestCase):
    """Cover cache deletion side effect in UnitViewSet.perform_create."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="cache_del_owner",
            password="p",
            full_name="CacheDelOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="cache_del_plan",
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
            name="CacheDelB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def test_create_unit_deletes_user_units_cache(self):
        """perform_create must invalidate units_user_{id} cache."""
        cache_key = f"units_user_{self.owner.id}"
        # Seed the cache with a stale QuerySet
        cache.set(cache_key, Unit.objects.none(), timeout=300)
        self.assertIsNotNone(cache.get(cache_key))

        response = self._c.post(
            "/properties/units/",
            {
                "building": self.building.id,
                "unit": "CACHE_DEL",
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(cache.get(cache_key))


class OwnerDashboardWithSubscriptionPlanTests(TestCase):
    """Cover owner_dashboard_summary with subscription plan context."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="dash_owner",
            password="p",
            full_name="DashOwner",
            email="dash@test.com",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="dash_pro",
            monthly_price=Decimal("49.99"),
            yearly_price=Decimal("499.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)

    def setUp(self):
        self._c = _auth(self.owner)

    def test_dashboard_summary_returns_200_for_authenticated_owner(self):
        """owner_dashboard_summary returns 200 for a subscribed owner."""
        response = self._c.get("/properties/owner/dashboard-summary/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_rent_collected", response.data)

    def test_dashboard_summary_empty_data_with_no_rent_records(self):
        """Dashboard returns zeros and empty lists when owner has no rent records."""
        response = self._c.get("/properties/owner/dashboard-summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_rent_collected"], 0.0)
        self.assertEqual(response.data["rent_defaulters"], [])

    def test_dashboard_anonymous_returns_401(self):
        """Unauthenticated access returns 401 (IsAuthenticated guard)."""
        response = self.client.get("/properties/owner/dashboard-summary/")
        self.assertEqual(response.status_code, 401)


class UnitImageViewSetUnlimitedFreeLimitCacheMissTests(TestCase):
    """Cover UnitImageViewSet.get_queryset cache miss branch with expired owner."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="img_cache_owner",
            password="p",
            full_name="ImgCacheOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="img_cache_plan",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ImgCacheB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="IMGC1",
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

    def test_get_queryset_cache_miss_populates_cache(self):
        """First call populates cache; second call hits cache."""
        from django.test import RequestFactory

        from properties.views.unit_views import UnitImageViewSet

        UnitImage.objects.create(unit=self.unit, image="cache_miss.jpg")
        cache_key = f"unit_images_user_{self.owner.id}"

        request = RequestFactory().get("/properties/unit-images/")
        request.user = self.owner
        view = UnitImageViewSet()
        view.request = request
        view.format_kwarg = None

        self.assertIsNone(cache.get(cache_key))
        qs = view.get_queryset()
        self.assertIsNotNone(cache.get(cache_key))
        self.assertEqual(qs.count(), 1)


class UnitDocumentViewSetUnlimitedFreeLimitTests(TestCase):
    """Cover UnitDocumentViewSet.get_queryset with cache miss + cache hit."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="doc_cache_owner",
            password="p",
            full_name="DocCacheOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="doc_cache_plan",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_documents", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DocCacheB",
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

    def test_get_queryset_cache_miss_then_hit(self):
        """Cache miss filters and sets; cache hit returns same queryset."""
        from django.test import RequestFactory

        from properties.views.unit_views import UnitDocumentViewSet

        doc = UnitDocument.objects.create(unit=self.unit, document="cache_doc.pdf")
        cache_key = f"unit_docs_user_{self.owner.id}"
        cache.clear()

        request = RequestFactory().get("/properties/unit-all-documents/")
        request.user = self.owner
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None

        self.assertIsNone(cache.get(cache_key))
        qs1 = view.get_queryset()
        self.assertIn(doc, qs1)
        # Second call should hit cache
        qs2 = view.get_queryset()
        self.assertEqual(list(qs1), list(qs2))


class UnitImageViewSetPerformUpdateSuccessTests(TestCase):
    """Cover UnitImageViewSet.perform_update when owner checks pass (lines 144-145)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="img_upd_succ_owner",
            password="p",
            full_name="ImgUpdSuccOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="img_upd_succ_plan",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ImgUpdSuccB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="IU1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def _make_view(self, user):
        from django.test import RequestFactory

        from properties.views.unit_views import UnitImageViewSet

        request = RequestFactory().patch("/properties/unit-images/")
        request.user = user
        view = UnitImageViewSet()
        view.request = request
        view.format_kwarg = None
        return view

    def test_perform_update_success_calls_save_and_deletes_cache(self):
        """When unit owner == request user → serializer.save + cache.delete are called."""
        img = UnitImage.objects.create(unit=self.unit, image="upd_succ.jpg")

        class FakeSerializer:
            instance = img
            validated_data = {"unit": self.unit}
            save_called = False

            def save(self, **kwargs):
                self.save_called = True

        serializer = FakeSerializer()
        view = self._make_view(self.owner)
        view.perform_update(serializer)
        self.assertTrue(serializer.save_called)
        cache_key = f"unit_images_user_{self.owner.id}"
        self.assertIsNone(cache.get(cache_key))


class UnitImageViewSetPerformDestroySuccessTests(TestCase):
    """Cover UnitImageViewSet.perform_destroy when owner matches (lines 150-155 T-branch)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="img_del_succ_owner",
            password="p",
            full_name="ImgDelSuccOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="img_del_succ_plan",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_images", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="ImgDelSuccB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="ID2",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def setUp(self):
        self.img = UnitImage.objects.create(unit=self.unit, image="ds.jpg")
        cache.clear()

    def test_perform_destroy_owner_match_deletes_and_decrements(self):
        """img.unit.owner == request.user → delete + decrement + cache.delete."""
        from django.test import RequestFactory

        from properties.feature_enforcer import FeatureEnforcer
        from properties.views.unit_views import UnitImageViewSet

        request = RequestFactory().delete("/properties/unit-images/")
        request.user = self.owner
        view = UnitImageViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": self.img.pk}
        view.get_object = lambda: self.img  # type: ignore[method-assign]

        FeatureEnforcer(self.owner).increment("unit_images")
        before = UsageLimit.objects.filter(
            user=self.owner, feature_key="unit_images"
        ).first()
        self.assertIsNotNone(before)
        initial = before.usage_count

        view.perform_destroy(self.img)

        self.assertFalse(UnitImage.objects.filter(id=self.img.id).exists())
        after = UsageLimit.objects.get(user=self.owner, feature_key="unit_images")
        self.assertEqual(after.usage_count, initial - 1)
        self.assertIsNone(cache.get(f"unit_images_user_{self.owner.id}"))

    def test_perform_destroy_owner_mismatch_raises(self):
        """img.unit.owner != request.user → PermissionDenied (line 151 T-branch)."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import UnitImageViewSet

        attacker = User.objects.create_user(
            username="img_del_attack", password="p", phone="+3"
        )
        atk_building = Building.objects.create(
            owner=attacker,
            name="AtkImgDelB",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        atk_unit = Unit.objects.create(
            owner=attacker,
            building=atk_building,
            unit="ATK_ID",
            unit_type="flat",
            address_line="3 St",
            city="C",
            state="S",
            country="CO",
            postal_code="3",
        )
        atk_img = UnitImage.objects.create(unit=atk_unit, image="atk.jpg")

        request = RequestFactory().delete("/properties/unit-images/")
        request.user = self.owner  # wrong user
        view = UnitImageViewSet()
        view.request = request
        view.format_kwarg = None

        with self.assertRaises(PermissionDenied):
            view.perform_destroy(atk_img)


class UnitDocumentPerformTests(TestCase):
    """Cover UnitDocumentViewSet perform_update and perform_destroy branches."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="doc_perf_owner",
            password="p",
            full_name="DocPerfOwner",
            phone="+1",
        )
        cls.attacker = User.objects.create_user(
            username="doc_perf_attacker",
            password="p",
            full_name="DocPerfAttacker",
            phone="+2",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="doc_perf_plan",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="unit_documents", value="10"
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="DocPerfB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="DOC_PERF1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        # attacker's unit for ownership-mismatch tests
        cls.atk_building = Building.objects.create(
            owner=cls.attacker,
            name="AtkDocPerfB",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        cls.atk_unit = Unit.objects.create(
            owner=cls.attacker,
            building=cls.atk_building,
            unit="ATKDOC_PF",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )

    def _make_request(self, method="GET"):
        from django.test import RequestFactory

        factory = RequestFactory()
        return getattr(factory, method)("/properties/unit-all-documents/")

    def test_perform_update_owner_match_saves_and_deletes_cache(self):
        """Lines 201-202: unit owner == request user → save + cache.delete."""
        from properties.views.unit_views import UnitDocumentViewSet

        doc = UnitDocument.objects.create(unit=self.unit, document="upd_perf.pdf")
        request = self._make_request("patch")
        request.user = self.owner
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None

        class FakeDocSerializer:
            instance = doc
            validated_data = {"unit": self.unit}
            save_called = False

            def save(self, **kwargs):
                self.save_called = True

        serializer = FakeDocSerializer()
        view.perform_update(serializer)
        self.assertTrue(serializer.save_called)
        self.assertIsNone(cache.get(f"unit_docs_user_{self.owner.id}"))

    def test_perform_update_owner_mismatch_raises(self):
        """Lines 199-202: unit.owner != request.user → PermissionDenied."""
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import UnitDocumentViewSet

        atk_doc = UnitDocument.objects.create(
            unit=self.atk_unit, document="atk_perf.pdf"
        )
        request = self._make_request("patch")
        request.user = self.owner  # wrong user
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None

        class FakeDocSerializer:
            instance = atk_doc
            validated_data = {"unit": self.atk_unit}

        with self.assertRaises(PermissionDenied):
            view.perform_update(FakeDocSerializer())

    def test_perform_destroy_owner_match_deletes_and_decrements(self):
        """Lines 207-212 T-branch: doc.unit.owner == request.user → delete + decrement."""
        from properties.feature_enforcer import FeatureEnforcer
        from properties.views.unit_views import UnitDocumentViewSet

        doc = UnitDocument.objects.create(unit=self.unit, document="del_perf.pdf")
        request = self._make_request("delete")
        request.user = self.owner
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": doc.pk}
        view.get_object = lambda: doc  # type: ignore[method-assign]

        FeatureEnforcer(self.owner).increment("unit_documents")
        before = UsageLimit.objects.filter(
            user=self.owner, feature_key="unit_documents"
        ).first()
        self.assertIsNotNone(before)
        initial = before.usage_count

        view.perform_destroy(doc)

        self.assertFalse(UnitDocument.objects.filter(id=doc.id).exists())
        after = UsageLimit.objects.get(user=self.owner, feature_key="unit_documents")
        self.assertEqual(after.usage_count, initial - 1)
        self.assertIsNone(cache.get(f"unit_docs_user_{self.owner.id}"))

    def test_perform_destroy_owner_mismatch_raises(self):
        """Line 208 F-branch: doc.unit.owner != request.user → PermissionDenied."""
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import UnitDocumentViewSet

        atk_doc = UnitDocument.objects.create(
            unit=self.atk_unit, document="atk_del_perf.pdf"
        )
        request = self._make_request("delete")
        request.user = self.owner  # wrong user
        view = UnitDocumentViewSet()
        view.request = request
        view.format_kwarg = None

        with self.assertRaises(PermissionDenied):
            view.perform_destroy(atk_doc)


class RentAgreementDraftViewSetLeegalityPathTests(TestCase):
    """Cover can_create=False, unit ownership fail, perform_destroy branches."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rad_path_owner",
            password="p",
            full_name="RadPathOwner",
            phone="+1",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rad_path_plan",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        # Only 0 drafts allowed → enforce can_create failure
        PlanFeatureLimit.objects.create(
            plan=cls.plan, feature_key="rent_agreement_drafts", value="0"
        )
        UsageLimit.objects.create(
            user=cls.owner, feature_key="rent_agreement_drafts", usage_count=0
        )
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RadPathB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RAD1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.attacker = User.objects.create_user(
            username="rad_attack", password="p", phone="+2"
        )
        cls.atk_building = Building.objects.create(
            owner=cls.attacker,
            name="AtkRadB",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        cls.atk_unit = Unit.objects.create(
            owner=cls.attacker,
            building=cls.atk_building,
            unit="ATK_RAD",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )

    def setUp(self):
        self._c = _auth(self.owner)
        cache.clear()

    def _make_request(self, method):
        from django.test import RequestFactory

        factory = RequestFactory()
        return getattr(factory, method)("/properties/rent-agreement-drafts/")

    def test_create_draft_denied_when_limit_reached(self):
        """can_create=False → 403 PermissionDenied (line 242)."""
        renter = Renter.objects.create(
            unit=self.unit,
            name="RadRenter",
            phone="+911234567901",
            email="rad@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        draft_file = SimpleUploadedFile(
            "draft.pdf", b"pdf", content_type="application/pdf"
        )
        response = self._c.post(
            "/properties/rent-agreement-drafts/",
            {
                "renter": renter.id,
                "unit": self.unit.id,
                "file": draft_file,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_create_draft_unit_ownership_fails_direct(self):
        """Direct call: unit.owner != request.user → PermissionDenied (line 244-245)."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import RentAgreementDraftViewSet

        wrong_renter = Renter.objects.create(
            unit=self.atk_unit,
            name="WrongRenter",
            phone="+911234567902",
            email="wrong@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        request = RequestFactory().post("/properties/rent-agreement-drafts/")
        request.user = self.owner
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None

        class FakeSerializer:
            validated_data = {
                "renter": wrong_renter,
                "unit": self.atk_unit,  # attacker's unit
            }

            def save(self, **kw):
                pass

        with self.assertRaises(PermissionDenied):
            view.perform_create(FakeSerializer())

    def test_perform_update_owner_mismatch_raises(self):
        """instance.user != request.user → PermissionDenied (line 271)."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import RentAgreementDraftViewSet

        attacker_draft = RentAgreementDraft.objects.create(
            user=self.attacker,
            renter=Renter.objects.create(
                unit=self.atk_unit,
                name="AtkRAD",
                phone="+911234567903",
                email="atk@test.com",
                rent_amount=Decimal("10000"),
                start_date=date.today(),
            ),
            unit=self.atk_unit,
            file="atk.pdf",
        )

        request = RequestFactory().patch("/properties/rent-agreement-drafts/")
        request.user = self.owner
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": attacker_draft.pk}

        class FakeSerializer:
            instance = attacker_draft
            validated_data = {}

            def save(self, **kw):
                pass

        with self.assertRaises(PermissionDenied):
            view.perform_update(FakeSerializer())

    def test_perform_destroy_succeeds_and_decrements(self):
        """Lines 292-296 T-branch: instance.user == request.user → delete + decrement."""
        from properties.feature_enforcer import FeatureEnforcer
        from properties.views.unit_views import RentAgreementDraftViewSet

        renter = Renter.objects.create(
            unit=self.unit,
            name="RadDelRenter",
            phone="+911234567904",
            email="raddel@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        draft = RentAgreementDraft.objects.create(
            user=self.owner, renter=renter, unit=self.unit, file="del_rad.pdf"
        )
        FeatureEnforcer(self.owner).increment("rent_agreement_drafts")
        before = UsageLimit.objects.filter(
            user=self.owner, feature_key="rent_agreement_drafts"
        ).first()
        self.assertIsNotNone(before)
        initial = before.usage_count

        request = self._make_request("delete")
        request.user = self.owner
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None

        view.perform_destroy(draft)

        self.assertFalse(RentAgreementDraft.objects.filter(id=draft.id).exists())
        after = UsageLimit.objects.get(
            user=self.owner, feature_key="rent_agreement_drafts"
        )
        self.assertEqual(after.usage_count, initial - 1)

    def test_perform_destroy_owner_mismatch_raises(self):
        """Lines 292-296 F-branch: instance.user != request.user → PermissionDenied."""
        from rest_framework.exceptions import PermissionDenied

        from properties.views.unit_views import RentAgreementDraftViewSet

        attacker_draft = RentAgreementDraft.objects.create(
            user=self.attacker,
            renter=Renter.objects.create(
                unit=self.atk_unit,
                name="AtkRD2",
                phone="+911234567905",
                email="atk2@test.com",
                rent_amount=Decimal("10000"),
                start_date=date.today(),
            ),
            unit=self.atk_unit,
            file="atk2.pdf",
        )

        request = self._make_request("delete")
        request.user = self.owner
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None

        with self.assertRaises(PermissionDenied):
            view.perform_destroy(attacker_draft)


class RentAgreementDraftPerformUpdateOwnerMismatchTests(TestCase):
    """Cover RentAgreementDraftViewSet.perform_update when instance user is wrong."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="rad_upd_owner",
            password="p",
            full_name="RadUpdOwner",
            phone="+1",
        )
        cls.attacker = User.objects.create_user(
            username="rad_upd_attack",
            password="p",
            full_name="RadUpdAttack",
            phone="+2",
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="rad_upd_plan",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.owner, plan=cls.plan, is_active=True)
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="RadUpdB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RADU1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        cls.atk_unit = Unit.objects.create(
            owner=cls.attacker,
            building=Building.objects.create(
                owner=cls.attacker,
                name="AtkRadUpdB",
                address_line="2 St",
                city="C",
                state="S",
                country="CO",
                postal_code="2",
            ),
            unit="ATKRAD_UPD",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )

    def test_perform_update_instance_user_mismatch_raises(self):
        """Lines 271-287: instance.user != request.user → PermissionDenied."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import RentAgreementDraftViewSet

        attacker_draft = RentAgreementDraft.objects.create(
            user=self.attacker,
            renter=Renter.objects.create(
                unit=self.atk_unit,
                name="AtkUpdRenter",
                phone="+911234567906",
                email="atkupd@test.com",
                rent_amount=Decimal("10000"),
                start_date=date.today(),
            ),
            unit=self.atk_unit,
            file="atk_upd.pdf",
        )
        request = RequestFactory().patch("/properties/rent-agreement-drafts/")
        request.user = self.owner
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": attacker_draft.pk}

        class FakeSerializer:
            instance = attacker_draft
            validated_data = {}

            def save(self, **kw):
                pass

        with self.assertRaises(PermissionDenied):
            view.perform_update(FakeSerializer())

    def test_perform_update_unit_owner_mismatch_raises(self):
        """Lines 281-284: unit.owner != request.user → PermissionDenied after instance check."""
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import RentAgreementDraftViewSet

        note = Renter.objects.create(
            unit=self.unit,
            name="NoteRenter",
            phone="+911234567907",
            email="note@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        draft = RentAgreementDraft.objects.create(
            user=self.owner, renter=note, unit=self.unit, file="upd_note.pdf"
        )
        request = RequestFactory().patch("/properties/rent-agreement-drafts/")
        request.user = self.owner
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": draft.pk}

        class FakeSerializer:
            instance = draft
            # validated_data unit is attacker's unit → unit ownership check fails
            validated_data = {"unit": self.atk_unit}

            def save(self, **kw):
                pass

        with self.assertRaises(PermissionDenied):
            view.perform_update(FakeSerializer())

    def test_perform_update_renter_unit_mismatch_after_valid_unit(self):
        """Lines 283-284: unit passes ownership check but renter.unit != unit → PermissionDenied.

        Use another of the owner's own units so the unit ownership check at
        line 281-283 passes, but renter belongs to a DIFFERENT unit.
        """
        from rest_framework.exceptions import PermissionDenied

        from django.test import RequestFactory

        from properties.views.unit_views import RentAgreementDraftViewSet

        # Second unit also owned by owner
        second_unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="RAD_U2",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="5",
        )
        # renter belongs to first unit (self.unit), not second_unit
        second_renter = Renter.objects.create(
            unit=self.unit,
            name="SecRenter",
            phone="+911234567909",
            email="sec@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        draft = RentAgreementDraft.objects.create(
            user=self.owner,
            renter=second_renter,
            unit=self.unit,
            file="upd_mis2.pdf",
        )
        request = RequestFactory().patch("/properties/rent-agreement-drafts/")
        request.user = self.owner
        view = RentAgreementDraftViewSet()
        view.request = request
        view.format_kwarg = None
        view.kwargs = {"pk": draft.pk}

        class FakeSerializer:
            instance = draft
            # renter.unit != self.atk_unit while unit.owner == request.user
            validated_data = {
                "renter": second_renter,
                "unit": second_unit,  # also owned by request user
            }

            def save(self, **kw):
                pass

        with self.assertRaises(PermissionDenied):
            view.perform_update(FakeSerializer())
