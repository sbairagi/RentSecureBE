import warnings

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import OwnerBankDetails


class TestOwnerBankDetailsDeprecationShim(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="deprecation_test_user",
            email="deprecation@example.com",
            password="testpass123",
        )

    def test_owner_bank_details_emits_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            OwnerBankDetails(owner=self.user)
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            self.assertTrue(
                any(
                    "deprecated" in str(warning.message)
                    for warning in deprecation_warnings
                ),
                "Expected DeprecationWarning when instantiating core.models.OwnerBankDetails",
            )

    def test_owner_bank_details_shim_maps_to_core_table(self):
        self.assertEqual(OwnerBankDetails._meta.db_table, "core_ownerbankdetails")

    def test_owner_bank_details_shim_has_all_fields(self):
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

    def test_owner_bank_details_shim_can_create_and_read(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            bank = OwnerBankDetails.objects.create(
                owner=self.user,
                bank_account_number="9999999999",
                ifsc_code="TEST0123",
            )
        self.assertIsNotNone(bank.pk)
        retrieved = OwnerBankDetails.objects.get(owner=self.user)
        self.assertEqual(retrieved.owner, self.user)
        self.assertEqual(retrieved.bank_account_number, "9999999999")
