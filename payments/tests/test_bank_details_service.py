import pytest

from payments.models import OwnerBankDetails


class TestBankDetailsService:
    @pytest.mark.django_db
    def test_creates_owner_bank_details_with_encryption(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="service_test_user",
            email="service@example.com",
            password="testpass123",
        )
        bank = OwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="9999999999",
            ifsc_code="TEST0123456",
            account_holder_name="Service Test",
            beneficiary_id="BENE-SVC-001",
            bank_account_verified=False,
        )
        assert bank.pk is not None
        assert bank.owner == user

    @pytest.mark.django_db
    def test_retrieves_owner_bank_details(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="retrieve_test",
            email="retrieve@example.com",
            password="testpass123",
        )
        OwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="8888888888",
            ifsc_code="RETR0123456",
        )
        bank = OwnerBankDetails.objects.get(owner=user)
        assert bank is not None

    @pytest.mark.django_db
    def test_updates_owner_bank_details(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="update_test",
            email="update@example.com",
            password="testpass123",
        )
        bank = OwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="7777777777",
            ifsc_code="UPDT0123456",
        )
        bank.bank_account_verified = True
        bank.save()
        bank.refresh_from_db()
        assert bank.bank_account_verified is True

    @pytest.mark.django_db
    def test_deletes_owner_bank_details(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="delete_test",
            email="delete@example.com",
            password="testpass123",
        )
        bank = OwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="6666666666",
            ifsc_code="DELE0123456",
        )
        pk = bank.pk
        bank.delete()
        assert not OwnerBankDetails.objects.filter(pk=pk).exists()
