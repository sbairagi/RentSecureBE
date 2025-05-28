# views.py
import random
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from twilio.rest import Client
from rest_framework.views import APIView
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework import generics, permissions
from .models import (User, OTP, SubscriptionPlan, UserSubscription, AddOnPurchase, PlanFeatureLimit, UsageLimit)
from .serializers import ( SubscriptionPlanSerializer, UserSubscriptionSerializer,AddOnPurchaseSerializer, 
                          PlanFeatureLimitSerializer, UsageLimitSerializer)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from referral_and_earn.models import Referral
from rest_framework.exceptions import PermissionDenied

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


class VerifyOTP(APIView):
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
# class ChangePasswordView(generics.UpdateAPIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def update(self, request, *args, **kwargs):
#         user = request.user
#         old_password = request.data.get("old_password")
#         new_password = request.data.get("new_password")

#         if not old_password or not new_password:
#             return Response({"error": "Both old and new passwords are required."}, status=400)

#         if not user.check_password(old_password):
#             return Response({"error": "Old password is incorrect."}, status=400)

#         if old_password == new_password:
#             return Response({"error": "New password must be different."}, status=400)

#         user.set_password(new_password)
#         user.save()
#         return Response({"message": "Password changed successfully."}, status=200)

# Reset Password
# class ResetPasswordView(APIView):
#     def post(self, request):
#         username_or_email = request.data.get("username")
#         new_password = request.data.get("new_password")

#         if not username_or_email or not new_password:
#             return Response({"error": "Username and new password are required."}, status=400)

#         try:
#             user = User.objects.get(username=username_or_email)
#         except User.DoesNotExist:
#             try:
#                 user = User.objects.get(email=username_or_email)
#             except User.DoesNotExist:
#                 return Response({"error": "User not found."}, status=404)

#         user.set_password(new_password)
#         user.save()
#         return Response({"message": "Password reset successful."}, status=200)





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
