# from services.whatsapp_service import send_whatsapp_message
# from rent.services import process_rent_payout
# from rent.models import RentRecord, Renter
from ai_platform_shared_be.services.cashfree_service import process_rent_payout
# from services.whatsapp_service import send_whatsapp_message
from notification.utils import send_whatsapp_message
from smartbot.services.agreement_service import generate_agreement_pdf
from properties.models import RentRecord, Renter
# from .services.agreement_service import generate_agreement_pdf
from .whatsapp_service import send_agreement_via_whatsapp
from .services.leegality_service import initiate_signature

def send_rent_reminder(renter_name):
    try:
        renter = Renter.objects.get(name__icontains=renter_name)
        msg = f"📢 Rent Reminder: Please pay your rent ₹{renter.rent_amount} for {renter.property.name}."
        send_whatsapp_message(renter.phone, msg)
        return f"✅ Reminder sent to {renter.name}"
    except Renter.DoesNotExist:
        return "❌ Renter not found."

def retry_payout(renter_name):
    try:
        rent = RentRecord.objects.filter(renter__name__icontains=renter_name).latest("created_at")
        result = process_rent_payout(rent)
        return f"✅ Payout retried: {result.get('status')}"
    except:
        return "❌ Could not retry payout."
    


def send_rent_agreement(renter_name):
    try:
        from django.conf import settings
        renter = Renter.objects.get(name__icontains=renter_name)
        rent = RentRecord.objects.filter(renter=renter).latest("created_at")
        
        pdf_path = generate_agreement_pdf(rent)
        
        # Move it to media or upload to S3
        from django.core.files.storage import default_storage
        with open(pdf_path, 'rb') as f:
            file_name = f"agreements/agreement_{rent.id}.pdf"
            default_storage.save(file_name, f)
            file_url = default_storage.url(file_name)

        send_agreement_via_whatsapp(renter, file_url)
        return f"✅ Agreement PDF sent to {renter.name} on WhatsApp."
    except Exception as e:
        return f"❌ Failed to send agreement: {str(e)}"
    

def send_agreement_for_signature(renter_name):
    try:
        renter = Renter.objects.get(name__icontains=renter_name)
        rent = RentRecord.objects.filter(renter=renter).latest("created_at")
        pdf_path = generate_agreement_pdf(rent)

        result = initiate_signature(renter, pdf_path)

        if result.get("status") == "success":
            rent.signature_request_id = result.get("documentId")
            rent.signature_status = "PENDING"
            rent.save()
            return f"📨 Signature request sent to {renter.name}!"
        return f"❌ Error: {result}"
    except Exception as e:
        return f"❌ Signature flow failed: {str(e)}"