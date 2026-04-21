from wealth_concierge_platform.models import RentRecord

# tasks.py (Celery or cron)

def poll_signature_status():
    rents = RentRecord.objects.filter(signature_status="PENDING")
    for rent in rents:
        status = check_signature_status(rent.signature_request_id)
        if status == "SIGNED":
            rent.signature_status = "SIGNED"
            rent.save()