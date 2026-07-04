# services/razorpay_service.py
from typing import Any

import razorpay  # type: ignore[import-untyped]

from django.conf import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_payment_link(rent_record: Any) -> str:
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
