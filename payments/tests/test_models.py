from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from payments.models import OwnerBankDetails


class TestOwnerBankDetailsModel(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="model_test_user",
            email="model@example.com",
            password="testpass123",
        )

    def test_owner_bank_details_matches_original_schema(self):
        expected_fields = {
            "id",
            "owner",
            "bank_account_number",
            "ifsc_code",
            "account_holder_name",
            "beneficiary_id",
            "bank_account_verified",
            "created_at",
            "updated_at",
        }
        actual_fields = {f.name for f in OwnerBankDetails._meta.get_fields()}
        self.assertEqual(actual_fields, expected_fields)

    def test_unique_together_user_and_bank_account(self):
        OwnerBankDetails.objects.create(
            owner=self.user,
            bank_account_number="1234567890",
            ifsc_code="ABCD0123456",
        )
        with self.assertRaises(IntegrityError):
            OwnerBankDetails.objects.create(
                owner=self.user,
                bank_account_number="1234567890",
                ifsc_code="ABCD0123456",
            )

    def test_user_foreign_key_uses_auth_user_model_string(self):
        owner_field = OwnerBankDetails._meta.get_field("owner")
        self.assertEqual(owner_field.remote_field.model, self.user_model)

    def test_db_table_is_payment_ownerbankdetails(self):
        self.assertEqual(OwnerBankDetails._meta.db_table, "payment_ownerbankdetails")

    def test_str_representation(self):
        bank = OwnerBankDetails(
            owner=self.user,
            bank_account_number="1234567890",
        )
        expected = f"{self.user.username} - 1234567890"
        self.assertEqual(str(bank), expected)
