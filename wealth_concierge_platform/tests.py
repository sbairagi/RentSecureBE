from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from .models import Property, Renter
from io import BytesIO
from PIL import Image

User = get_user_model()

# ✅ Helper function to generate a valid dummy image file
def get_dummy_image(name="test.jpg"):
    image = Image.new("RGB", (1, 1), color=(255, 255, 255))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


class PropertyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

    def test_create_property(self):
        dummy_file = SimpleUploadedFile("id.pdf", b"file_content", content_type="application/pdf")
        dummy_image = get_dummy_image()

        data = {
            "owner": self.user.id,
            "title": "Test Property",
            "address_line": "123 Test Street",
            "landmark": "Near Park",
            "city": "Testville",
            "state": "TS",
            "country": "Testland",
            "postal_code": "123456",
            "property_type": "flat",
            "property_image": dummy_image,
            "id_proof": dummy_file,
            "is_vacant": True,
            "is_verified": False,
            "rent_due_reminder": True,
            "agreement_expiry_reminder": True,
        }

        response = self.client.post("/wealth_concierge_platform/properties/", data, format='multipart')
        print(response.status_code, response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CaretakerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser2', password='password')
        self.client.force_authenticate(user=self.user)
        self.property = Property.objects.create(
            owner=self.user,
            title="Test Property",
            address_line="123 Test Street",
            city="Testville",
            state="TS",
            country="Testland",
            postal_code="123456",
            property_type="flat",
            id_proof=SimpleUploadedFile("id.pdf", b"proof", content_type="application/pdf")
        )

    def test_create_caretaker(self):
        dummy_id = SimpleUploadedFile("id.pdf", b"id content", content_type="application/pdf")
        dummy_image = get_dummy_image()

        data = {
            "property": self.property.id,
            "name": "John Doe",
            "phone": "1234567890",
            "caretaker_image": dummy_image,
            "id_proof": dummy_id,
            "address_line": "456 Another St",
            "city": "Testville",
            "state": "TS",
            "country": "Testland",
            "postal_code": "123456",
        }

        response = self.client.post("/wealth_concierge_platform/caretakers/", data, format='multipart')
        print(response.status_code, response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class RenterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser3', password='password')
        self.client.force_authenticate(user=self.user)
        self.property = Property.objects.create(
            owner=self.user,
            title="Test Property",
            address_line="123 Test Street",
            city="Testville",
            state="TS",
            country="Testland",
            postal_code="123456",
            property_type="flat",
            id_proof=SimpleUploadedFile("id.pdf", b"proof", content_type="application/pdf")
        )

    def test_create_renter(self):
        dummy_id = SimpleUploadedFile("id.pdf", b"id content", content_type="application/pdf")
        dummy_agreement = SimpleUploadedFile("agreement.pdf", b"agreement content", content_type="application/pdf")
        dummy_image = get_dummy_image()

        data = {
            "property": self.property.id,
            "name": "Jane Doe",
            "phone": "9876543210",
            "renter_image": dummy_image,
            "id_proof": dummy_id,
            "rent_agreement": dummy_agreement,
            "rent_amount": "1500.00",
            "start_date": "2024-01-01",
        }

        response = self.client.post("/wealth_concierge_platform/renters/", data, format='multipart')
        print(response.status_code, response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class RentRecordTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser4', password='password')
        self.client.force_authenticate(user=self.user)
        self.property = Property.objects.create(
            owner=self.user,
            title="Test Property",
            address_line="123 Test Street",
            city="Testville",
            state="TS",
            country="Testland",
            postal_code="123456",
            property_type="flat",
            id_proof=SimpleUploadedFile("id.pdf", b"proof", content_type="application/pdf")
        )
        self.renter = Renter.objects.create(
            property=self.property,
            name="Alice Smith",
            phone="1122334455",
            id_proof=SimpleUploadedFile("id.pdf", b"id", content_type="application/pdf"),
            rent_agreement=SimpleUploadedFile("agree.pdf", b"agree", content_type="application/pdf"),
            rent_amount=1200.00,
            start_date="2024-01-01"
        )

    def test_create_rent_record(self):
        data = {
            "renter": self.renter.id,
            "property": self.property.id,
            "rent_month": "2024-05-01",
            "amount_paid": "1200.00",
            "date_paid": "2024-05-05",
            "payment_mode": "UPI",
        }

        response = self.client.post("/wealth_concierge_platform/rent-records/", data)
        print(response.status_code, response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
