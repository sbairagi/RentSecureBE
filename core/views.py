from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import App, AILog
from .serializers import RegisterSerializer, AppSerializer, AILogSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .models import User
# User = get_user_model()

# Register
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

# Manual login using JWT
class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            })
        return Response({"error": "Invalid Credentials"}, status=400)

# change Password
class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"error": "Both old and new passwords are required."}, status=400)

        if not check_password(old_password, user.password):
            return Response({"error": "Old password is incorrect."}, status=400)

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

# App list
class AppListView(generics.ListAPIView):
    queryset = App.objects.all()
    serializer_class = AppSerializer
    permission_classes = [permissions.IsAuthenticated]

# Create or view AI logs
class AILogListCreateView(generics.ListCreateAPIView):
    serializer_class = AILogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AILog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)