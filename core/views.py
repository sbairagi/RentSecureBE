# views.py
import random
from notification.services.rent_notify_service import send_payout_notification
from notification.services.voice_note_service import generate_voice_note
from notification.services.whatsapp_service import send_whatsapp_audio
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from twilio.rest import Client
from rest_framework.views import APIView
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework import generics, permissions

from core.utils.export_utils import generate_owner_rent_report
from wealth_concierge_platform.utils import generate_rent_invoice_pdf
from .models import (User, OTP, SubscriptionPlan, UserSubscription, AddOnPurchase, PlanFeatureLimit, UsageLimit)
from .serializers import ( SubscriptionPlanSerializer, UserSubscriptionSerializer,AddOnPurchaseSerializer, 
                          PlanFeatureLimitSerializer, UsageLimitSerializer)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from referral_and_earn.models import Referral
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import Group

# python3 manage.py runserver 0.0.0.0:8000

ENV = "development"  # Set this to "production" in live

def send_otp(phone_number, code):
    if ENV == "production":
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = f"Your verification code is {code}"
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
    else:
        print(f"[MOCK OTP to {phone_number}] Your OTP is {code}")


class SendOTP(APIView):
    def post(self, request):
        phone = request.data.get("phone")
        referral_code = request.data.get("referral_code", "").strip()

        if not phone:
            return Response({"error": "Phone number required"}, status=400)

        # Prevent spamming (resend OTP limit: 60 seconds)
        recent_otp = OTP.objects.filter(phone_number=phone).order_by('-created_at').first()
        if recent_otp and (timezone.now() - recent_otp.created_at).seconds < 60:
            return Response({"error": "Wait before requesting another OTP"}, status=429)

        code = str(random.randint(100000, 999999))

        OTP.objects.create(phone_number=phone, code=code, referral_code=referral_code)
        send_otp(phone, code)

        return Response({"message": "OTP sent"}, status=200)


class OwnerVerifyOTP(APIView):
    def post(self, request):
        phone = request.data.get("phone")
        code = request.data.get("otp")

        if not phone or not code:
            return Response({"error": "Phone and OTP required"}, status=400)

        # Filter only unverified OTPs
        otp = OTP.objects.filter(
            phone_number=phone,
            code=code,
            is_verified=False
        ).order_by('-created_at').first()

        if otp and (timezone.now() - otp.created_at) < timedelta(minutes=5):
            otp.is_verified = True
            otp.save()

            user, created = User.objects.get_or_create(phone=phone, defaults={"username": phone})
            user.is_phone_verified = True
            user.save()
            group = Group.objects.get(name='tenant')
            user.groups.add(group)

            # Referral logic
            if otp.referral_code:
                try:
                    referrer_referral = Referral.objects.get(referral_code=otp.referral_code)
                    referrer = referrer_referral.user

                    # Create referral object for this user if doesn't exist
                    referral, _ = Referral.objects.get_or_create(user=user)
                    if not referral.referred_by:
                        referral.referred_by = referrer
                        referral.save()

                        # Reward the referrer
                        referrer_referral.bonus_earned += 500
                        referrer_referral.save()

                except Referral.DoesNotExist:
                    return Response({'error': 'Invalid referral code'}, status=400)

            # Delete all old OTPs for this user except the one used
            OTP.objects.filter(phone_number=phone).exclude(id=otp.id).delete()

            # JWT token
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "phone": user.phone,
                }
            })

        return Response({"error": "Invalid or expired OTP"}, status=400)


class RenterVerifyOTP(APIView):
    def post(self, request):
        phone = request.data.get("phone")
        code = request.data.get("otp")

        if not phone or not code:
            return Response({"error": "Phone and OTP required"}, status=400)

        # Filter only unverified OTPs
        otp = OTP.objects.filter(
            phone_number=phone,
            code=code,
            is_verified=False
        ).order_by('-created_at').first()

        if otp and (timezone.now() - otp.created_at) < timedelta(minutes=5):
            otp.is_verified = True
            otp.save()

            user, created = User.objects.get_or_create(phone=phone, defaults={"username": phone})
            user.is_phone_verified = True
            user.save()

            group = Group.objects.get(name='renter')
            user.groups.add(group)

            # Referral logic
            if otp.referral_code:
                try:
                    referrer_referral = Referral.objects.get(referral_code=otp.referral_code)
                    referrer = referrer_referral.user

                    # Create referral object for this user if doesn't exist
                    referral, _ = Referral.objects.get_or_create(user=user)
                    if not referral.referred_by:
                        referral.referred_by = referrer
                        referral.save()

                        # Reward the referrer
                        referrer_referral.bonus_earned += 500
                        referrer_referral.save()

                except Referral.DoesNotExist:
                    return Response({'error': 'Invalid referral code'}, status=400)

            # Delete all old OTPs for this user except the one used
            OTP.objects.filter(phone_number=phone).exclude(id=otp.id).delete()

            # JWT token
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "phone": user.phone,
                }
            })

        return Response({"error": "Invalid or expired OTP"}, status=400)
    



# change Password
class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"error": "Both old and new passwords are required."}, status=400)

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect."}, status=400)

        if old_password == new_password:
            return Response({"error": "New password must be different."}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully."}, status=200)

# Reset Password
class ResetPasswordView(APIView):
    def post(self, request):
        username_or_email = request.data.get("username")
        new_password = request.data.get("new_password")

        if not username_or_email or not new_password:
            return Response({"error": "Username and new password are required."}, status=400)

        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=404)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password reset successful."}, status=200)





# Global Plans & Limits (public for listing)
class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]  

class PlanFeatureLimitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlanFeatureLimit.objects.all()
    serializer_class = PlanFeatureLimitSerializer
    permission_classes = [permissions.AllowAny]

class UserSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can't edit another user's subscription.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can't delete another user's subscription.")
        instance.delete()

class AddOnPurchaseViewSet(viewsets.ModelViewSet):
    queryset = AddOnPurchase.objects.all()
    serializer_class = AddOnPurchaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AddOnPurchase.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can't modify another user's purchase.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can't delete another user's purchase.")
        instance.delete()

class UsageLimitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UsageLimit.objects.all()
    serializer_class = UsageLimitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UsageLimit.objects.filter(user=self.request.user)



# views.py

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from wealth_concierge_platform.models import RentRecord

@csrf_exempt
def cashfree_payout_webhook(request):
    if request.method == "POST":
        payload = json.loads(request.body)
        transfer_id = payload.get("transferId")
        status = payload.get("event")

        try:
            rent = RentRecord.objects.get(payout_reference=transfer_id)
            if status == "TRANSFER_SUCCESS":
                rent.payout_status = "SUCCESS"
            elif status == "TRANSFER_FAILED":
                rent.payout_status = "FAILED"
            rent = rent.save()

            # 🔔 WhatsApp Alert After Saving
            owner = rent.renter.property.owner
            phone = owner.profile.whatsapp_number  # Make sure this is stored in +91 format

            if phone:
                send_payout_notification(rent)
        except RentRecord.DoesNotExist:
            return JsonResponse({"error": "Invalid transfer ID"}, status=404)

        return JsonResponse({"message": "Webhook received"}, status=200)

    return JsonResponse({"error": "Invalid method"}, status=405)


# views.py

import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from wealth_concierge_platform.models import RentRecord

@csrf_exempt
def create_rent_payment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        rent_id = data["rent_id"]

        rent = RentRecord.objects.get(id=rent_id)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": int(rent.amount * 100),  # In paise
            "currency": "INR",
            "receipt": f"rent_{rent.id}",
            "payment_capture": 1
        })

        rent.razorpay_order_id = razorpay_order["id"]
        rent.save()

        return JsonResponse({
            "order_id": razorpay_order["id"],
            "amount": rent.amount,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID
        })

from ai_platform_shared_be.services.cashfree_service  import process_rent_payout

# @csrf_exempt
# def razorpay_webhook(request):
#     data = json.loads(request.body)
#     event = data.get("event")

#     if event == "payment.captured":
#         razorpay_order_id = data["payload"]["payment"]["entity"]["order_id"]
#         rent = RentRecord.objects.get(razorpay_order_id=razorpay_order_id)

#         rent.razorpay_payment_status = "PAID"
#         rent.save()

#         # Now auto-trigger payout
#         process_rent_payout(rent)

#     return JsonResponse({"status": "ok"})


# https://yourdomain.com/api/razorpay/webhook/


# ✅ 5. Frontend Integration (Razorpay Checkout)
# const options = {
#   key: "<%= key_id %>",
#   amount: amount * 100,
#   currency: "INR",
#   name: "Rent Payment",
#   order_id: order_id,
#   handler: function (response) {
#     alert("Payment Successful");
#   }
# };

# const rzp1 = new Razorpay(options);
# rzp1.open();



import json, hmac, hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from wealth_concierge_platform.models import RentRecord
from ai_platform_shared_be.services.cashfree_service import process_rent_payout

@csrf_exempt
def razorpay_webhook(request):
    # Get raw body and signature
    body = request.body
    signature = request.headers.get('X-Razorpay-Signature')

    # ✅ Step 1: Verify signature
    secret = bytes(settings.RAZORPAY_WEBHOOK_SECRET, 'utf-8')
    expected_signature = hmac.new(secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        return HttpResponseBadRequest("Invalid signature!")

    # ✅ Step 2: Process webhook if verified
    data = json.loads(body)
    event = data.get("event")

    if event == "payment.captured":
        razorpay_order_id = data["payload"]["payment"]["entity"]["order_id"]

        try:
            rent = RentRecord.objects.get(razorpay_order_id=razorpay_order_id)
        except RentRecord.DoesNotExist:
            return JsonResponse({"error": "RentRecord not found"}, status=404)

        rent.payment_status = "PAID"
        rent.save()

        # ✅ Trigger payout
        process_rent_payout(rent)

    return JsonResponse({"status": "ok"})



@csrf_exempt
def razorpay_webhook(request):
    data = json.loads(request.body)
    event = data.get("event")

    if event == "payment_link.paid":
        ref_id = data["payload"]["payment_link"]["entity"]["reference_id"]
        rent = RentRecord.objects.get(id=ref_id)
        rent.payment_status = "PAID"

        # iska use karna per abhi nahi samaz aaraha is liye comment kara hai isko touch mat karna 
        # pdf_path = generate_rent_invoice_pdf(rent)
        # upload_path = upload_to_s3(pdf_path, f"invoices/rent_{rent.id}.pdf")  # or store locally
        # rent.invoice_url = upload_path
        rent.save()

        # ✅ Trigger payout
        process_rent_payout(rent)

    return JsonResponse({"status": "ok"})



from .models import OwnerBankDetails
from ai_platform_shared_be.services.cashfree_service import delete_beneficiary
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

# views.py
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_owner_bank_details(request):
    data = request.data
    owner = request.user

    # Validate input
    required_fields = ["account_number", "ifsc_code", "account_holder_name"]
    if not all(data.get(field) for field in required_fields):
        return Response({"error": "Missing fields"}, status=400)

    # Delete old beneficiary on Cashfree
    try:
        bank = OwnerBankDetails.objects.get(owner=owner)
        if bank.beneficiary_id:
            delete_beneficiary(bank.beneficiary_id)
    except OwnerBankDetails.DoesNotExist:
        bank = OwnerBankDetails(owner=owner)

    # Register new beneficiary
    bene_id = f"owner_{owner.id}_{uuid.uuid4().hex[:8]}"
    response = register_beneficiary(
        bene_id=bene_id,
        name=data["account_holder_name"],
        account_number=data["account_number"],
        ifsc=data["ifsc_code"]
    )

    if response.get("subCode") != "200":
        return Response({"error": "Bank registration failed", "response": response}, status=400)

    # Save new bank details
    bank.account_number = data["account_number"]
    bank.ifsc_code = data["ifsc_code"]
    bank.account_holder_name = data["account_holder_name"]
    bank.beneficiary_id = bene_id
    bank.save()

    # Retry all failed payouts for this owner
    RentRecord.objects.filter(
        renter__property__owner=owner,
        payout_status="FAILED"
    ).update(payout_status="READY_TO_RETRY")

    return Response({"message": "Bank details updated & pending payouts marked for retry ✅"})




# from services.razorpay_service import create_payment_link

# # After saving rent record
# link = create_payment_link(rent)
# rent.payment_link = link
# rent.save()

# # Optional: WhatsApp message
# send_whatsapp_message(rent.renter.phone, f"📩 Pay your rent: {link}")



# views/owner.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
# from rent.models import RentRecord
from wealth_concierge_platform.models import RentRecord

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rent_inflow_summary(request):
    owner = request.user
    total_received = RentRecord.objects.filter(
        renter__property__owner=owner,
        payment_status='PAID'
    ).aggregate(total=Sum('amount'))['total'] or 0

    pending_count = RentRecord.objects.filter(
        renter__property__owner=owner,
        payment_status='DUE'
    ).count()

    failed_payouts = RentRecord.objects.filter(
        renter__property__owner=owner,
        payout_status='FAILED'
    ).count()

    return Response({
        "total_received": total_received,
        "pending_payments": pending_count,
        "failed_payouts": failed_payouts
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def owner_rent_records(request):
    owner = request.user
    rents = RentRecord.objects.filter(renter__property__owner=owner).select_related(
        'renter', 'renter__property'
    ).order_by('-due_date')

    return Response([
        {
            "property": r.renter.property.title,
            "renter": r.renter.full_name,
            "month": r.due_date.strftime("%B %Y"),
            "rent": r.amount,
            "status": r.payment_status,
            "payout_status": r.payout_status
        }
        for r in rents
    ])


# views/owner.py
from django.http import HttpResponse
# from utils.export_utils import generate_owner_rent_report

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_rent_excel(request):
    file = generate_owner_rent_report(request.user)
    response = HttpResponse(file, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="rent_report.xlsx"'
    return response