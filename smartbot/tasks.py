from properties.models import RentRecord
from smartbot.services.leegality_service import check_signature_status

# tasks.py (Celery or cron)


def poll_signature_status():
    rents = RentRecord.objects.filter(signature_status="PENDING")
    for rent in rents:
        status = check_signature_status(rent.signature_request_id)
        if status == "SIGNED":
            rent.signature_status = "SIGNED"
            rent.save()
