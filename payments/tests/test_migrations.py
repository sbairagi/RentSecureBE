import importlib
import time

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase

from payments.models import OwnerBankDetails


class TestOwnerBankDetailsMigration(TestCase):
    def test_migration_forward_copies_all_rows(self):
        from core.models import OwnerBankDetails as CoreOwnerBankDetails

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="migration_test_user",
            email="test@example.com",
            password="testpass123",
        )
        core_record = CoreOwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="1234567890",
            ifsc_code="ABCD0123456",
            account_holder_name="Test User",
            beneficiary_id="BENE-001",
            bank_account_verified=True,
        )

        migration_module = importlib.import_module(
            "payments.migrations.0004_migrate_ownerbankdetails"
        )
        migration_module.copy_owner_bank_details(apps, None)

        payment_record = OwnerBankDetails.objects.get(owner=user)
        self.assertEqual(payment_record.owner_id, core_record.owner_id)
        self.assertEqual(
            payment_record.bank_account_number, core_record.bank_account_number
        )
        self.assertEqual(payment_record.ifsc_code, core_record.ifsc_code)
        self.assertEqual(
            payment_record.account_holder_name, core_record.account_holder_name
        )
        self.assertEqual(payment_record.beneficiary_id, core_record.beneficiary_id)
        self.assertEqual(
            payment_record.bank_account_verified, core_record.bank_account_verified
        )
        self.assertEqual(payment_record.created_at, core_record.created_at)
        self.assertEqual(payment_record.updated_at, core_record.updated_at)

    def test_migration_forward_preserves_encrypted_fields(self):
        from core.models import OwnerBankDetails as CoreOwnerBankDetails

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="encryption_test_user",
            email="enc@example.com",
            password="testpass123",
        )

        core_record = CoreOwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="SECRET123",
            ifsc_code="SECRETIFSC",
        )

        migration_module = importlib.import_module(
            "payments.migrations.0004_migrate_ownerbankdetails"
        )
        migration_module.copy_owner_bank_details(apps, None)

        payment_record = OwnerBankDetails.objects.get(owner=user)
        self.assertEqual(
            payment_record.bank_account_number, core_record.bank_account_number
        )
        self.assertEqual(payment_record.ifsc_code, core_record.ifsc_code)

    def test_migration_forward_preserves_user_links(self):
        from core.models import OwnerBankDetails as CoreOwnerBankDetails

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="user_link_test",
            email="link@example.com",
            password="testpass123",
        )

        CoreOwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="1111111111",
            ifsc_code="2222222222",
        )

        migration_module = importlib.import_module(
            "payments.migrations.0004_migrate_ownerbankdetails"
        )
        migration_module.copy_owner_bank_details(apps, None)

        payment_record = OwnerBankDetails.objects.get(owner=user)
        self.assertEqual(payment_record.owner_id, user.id)

    def test_migration_forward_preserves_timestamps(self):
        from core.models import OwnerBankDetails as CoreOwnerBankDetails

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="timestamp_test",
            email="ts@example.com",
            password="testpass123",
        )

        core_record = CoreOwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="3333333333",
            ifsc_code="4444444444",
        )

        migration_module = importlib.import_module(
            "payments.migrations.0004_migrate_ownerbankdetails"
        )
        migration_module.copy_owner_bank_details(apps, None)

        payment_record = OwnerBankDetails.objects.get(owner=user)
        self.assertEqual(payment_record.owner_id, core_record.owner_id)
        self.assertEqual(
            payment_record.bank_account_number, core_record.bank_account_number
        )
        self.assertEqual(payment_record.ifsc_code, core_record.ifsc_code)
        self.assertEqual(payment_record.created_at, core_record.created_at)
        self.assertEqual(payment_record.updated_at, core_record.updated_at)

    def test_migration_reverse_restores_data(self):
        from core.models import OwnerBankDetails as CoreOwnerBankDetails

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="reverse_test",
            email="reverse@example.com",
            password="testpass123",
        )

        CoreOwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="5555555555",
            ifsc_code="6666666666",
        )

        migration_module = importlib.import_module(
            "payments.migrations.0004_migrate_ownerbankdetails"
        )
        migration_module.copy_owner_bank_details(apps, None)
        self.assertEqual(OwnerBankDetails.objects.count(), 1)

        migration_module.reverse_copy(apps, None)
        self.assertEqual(OwnerBankDetails.objects.count(), 0)
        self.assertEqual(CoreOwnerBankDetails.objects.count(), 1)

    def test_migration_on_empty_database(self):
        self.assertEqual(OwnerBankDetails.objects.count(), 0)
        migration_module = importlib.import_module(
            "payments.migrations.0004_migrate_ownerbankdetails"
        )
        migration_module.copy_owner_bank_details(apps, None)
        self.assertEqual(OwnerBankDetails.objects.count(), 0)

    def test_migration_on_production_like_data(self):
        from core.models import OwnerBankDetails as CoreOwnerBankDetails

        user_model = get_user_model()
        users = []
        core_records = []
        for i in range(10):
            user = user_model.objects.create_user(
                username=f"prod_test_user_{i}",
                email=f"prod{i}@example.com",
                password="testpass123",
            )
            users.append(user)
            record = CoreOwnerBankDetails.objects.create(
                owner=user,
                bank_account_number=f"ACCOUNT{i:010d}",
                ifsc_code=f"IFSC{i:07d}",
                account_holder_name=f"User {i}",
                beneficiary_id=f"BENE-{i:04d}",
                bank_account_verified=(i % 2 == 0),
            )
            core_records.append(record)

        migration_module = importlib.import_module(
            "payments.migrations.0004_migrate_ownerbankdetails"
        )
        start = time.time()
        migration_module.copy_owner_bank_details(apps, None)
        elapsed = time.time() - start

        self.assertLess(elapsed, 30, "Migration took too long")
        self.assertEqual(
            OwnerBankDetails.objects.count(),
            CoreOwnerBankDetails.objects.count(),
        )
        for core_record in core_records:
            payment_record = OwnerBankDetails.objects.get(owner=core_record.owner)
            self.assertEqual(
                payment_record.bank_account_number, core_record.bank_account_number
            )
            self.assertEqual(payment_record.ifsc_code, core_record.ifsc_code)
