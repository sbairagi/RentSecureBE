import os

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rentsecure_be.settings")
import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import TestCase, override_settings  # noqa: E402

from core.models import (  # noqa: E402
    PlanFeatureLimit,
    SubscriptionPlan,
    UserSubscription,
)
from properties.models import Building, Unit  # noqa: E402

User = get_user_model()


@override_settings(ALLOWED_HOSTS=["*"])
class DebugTest(TestCase):
    def test_debug(self):
        owner = User.objects.create_user(
            username="img_test",
            password="testpass123",  # noqa: S106
            full_name="ImgTest",
            phone="+1",
        )
        plan = SubscriptionPlan.objects.create(
            name="img_pro2", monthly_price="29.99", yearly_price="299.99"
        )
        UserSubscription.objects.create(user=owner, plan=plan, is_active=True)
        PlanFeatureLimit.objects.create(plan=plan, feature_key="max_units", value="10")
        PlanFeatureLimit.objects.create(
            plan=plan, feature_key="unit_images", value="10"
        )
        building = Building.objects.create(
            owner=owner,
            name="IMGB2",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        unit = Unit.objects.create(
            owner=owner,
            building=building,
            unit="IMG2",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

        c = APIClient()
        c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(owner).access_token}"
        )
        image_file = SimpleUploadedFile(
            "test.jpg", b"fake-image", content_type="image/jpeg"
        )
        response = c.post(
            "/properties/unit-images/", {"unit": unit.id, "image": image_file}
        )
        print("Status:", response.status_code)
        print(
            "Data:",
            dict(response.data) if hasattr(response, "data") else response.content,
        )
