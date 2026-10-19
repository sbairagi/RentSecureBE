"""Regression coverage for plan usage counters updated by model signals."""

from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model

from core.models import PlanFeatureLimit, SubscriptionPlan, UsageLimit, UserSubscription
from properties.models import Building, Renter, Unit

User = get_user_model()


class UsageCounterSyncTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="usage_sync_owner",
            password="StrongPassword!948",
            full_name="Usage Sync Owner",
            phone="+919876543219",
        )
        self.plan = SubscriptionPlan.objects.create(
            name="usage_sync_plan",
            monthly_price="0.00",
            yearly_price="0.00",
        )
        UserSubscription.objects.create(
            user=self.owner,
            plan=self.plan,
            is_active=True,
        )
        for feature in ("max_buildings", "max_units", "max_renters"):
            PlanFeatureLimit.objects.create(
                plan=self.plan,
                feature_key=feature,
                value="2",
            )
        self.client.force_authenticate(self.owner)

    def usage(self, feature):
        record = UsageLimit.objects.get(user=self.owner, feature_key=feature)
        return record.usage_count

    def test_property_unit_and_renter_crud_tracks_usage_once(self):
        building_response = self.client.post(
            "/api/buildings/",
            {
                "name": "Usage Sync Building",
                "address_line": "1 Test Road",
                "city": "Pune",
                "state": "Maharashtra",
                "country": "India",
                "postal_code": "411001",
            },
            format="json",
        )
        self.assertEqual(building_response.status_code, 201)
        building_id = building_response.data["id"]
        self.assertEqual(self.usage("max_buildings"), 1)

        unit_response = self.client.post(
            "/api/units/",
            {
                "building": building_id,
                "unit": "QA-1",
                "unit_type": "flat",
                "status": "vacant",
                "address_line": "1 Test Road",
                "city": "Pune",
                "state": "Maharashtra",
                "country": "India",
                "postal_code": "411001",
            },
            format="json",
        )
        self.assertEqual(unit_response.status_code, 201)
        unit_id = unit_response.data["id"]
        self.assertEqual(self.usage("max_units"), 1)

        renter_response = self.client.post(
            "/api/renters/",
            {
                "unit": unit_id,
                "name": "Usage Sync Renter",
                "email": "usage-sync-renter@example.com",
                "phone": "+919876543218",
                "rent_amount": "10000.00",
                "start_date": "2026-10-18",
                "status": "active",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(renter_response.status_code, 201)
        renter_id = renter_response.data["id"]
        self.assertEqual(self.usage("max_renters"), 1)

        self.assertEqual(
            self.client.delete(f"/api/renters/{renter_id}/").status_code, 204
        )
        self.assertEqual(self.usage("max_renters"), 0)
        self.assertEqual(self.client.delete(f"/api/units/{unit_id}/").status_code, 204)
        self.assertEqual(self.usage("max_units"), 0)
        self.assertEqual(
            self.client.delete(f"/api/buildings/{building_id}/").status_code,
            204,
        )
        self.assertEqual(self.usage("max_buildings"), 0)

        self.assertFalse(Building.objects.filter(pk=building_id).exists())
        self.assertFalse(Unit.objects.filter(pk=unit_id).exists())
        self.assertFalse(Renter.objects.filter(pk=renter_id).exists())
