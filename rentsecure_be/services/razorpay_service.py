# services/razorpay_service.py
from typing import Any

from payments.adapters.razorpay import RazorpayAdapter
from payments.services.payment_service import PaymentService


def create_payment_link(rent_record: Any) -> str:
    return PaymentService(RazorpayAdapter()).create_payment_link(rent_record)
