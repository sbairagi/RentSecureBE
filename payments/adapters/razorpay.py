from typing import Any

import razorpay  # type: ignore[import-untyped]

from django.conf import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class RazorpayAdapter:
    """Razorpay payment adapter.

    Implements PaymentGateway using the existing Razorpay payment
    link creation logic.
    """

    def create_payment_link(self, rent_record: Any) -> str:
        renter = rent_record.renter

        response = client.payment_link.create(
            {
                "amount": int(rent_record.amount * 100),  # in paise
                "currency": "INR",
                "accept_partial": False,
                "description": f"Rent for {rent_record.month} {rent_record.year}",
                "customer": {
                    "name": renter.name,
                    "contact": renter.phone,
                    "email": renter.email,
                },
                "notify": {"sms": True, "email": True},
                "reminder_enable": True,
                "callback_url": "https://yourdomain.com/api/rent/payment-callback/",
                "callback_method": "get",
            }
        )

        link: str = response["short_url"]
        return link

    def process_payout(self, rent: Any) -> dict[str, Any]:
        raise NotImplementedError

    def register_beneficiary(self, bank_details: Any) -> dict[str, Any]:
        raise NotImplementedError

    def delete_beneficiary(self, beneficiary_id: str) -> dict[str, Any]:
        raise NotImplementedError
