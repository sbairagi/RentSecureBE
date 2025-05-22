from rest_framework import serializers
# from django.contrib.auth import get_user_model
from .models import App, UserApp, AILog

from core.models import User
# User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'phone']

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email", "password", "full_name", "phone")
        extra_kwargs = {
            "password": {"write_only": True}
        }

    # def create(self, validated_data):
    #     return User.objects.create_user(
    #         username=validated_data["username"],
    #         email=validated_data["email"],
    #         full_name=validated_data.get("full_name", ""),
    #         phone=validated_data.get("phone", ""),
    #         password=validated_data["password"]
    #     )
    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            full_name=validated_data.get("full_name", ""),
            phone=validated_data.get("phone", ""),
            password=validated_data["password"]  # this hashes automatically
        )

class AppSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = ['id', 'name', 'slug']

class UserAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserApp
        fields = ['user', 'app', 'access_granted']

class AILogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AILog
        fields = ['id', 'user', 'app', 'prompt', 'response', 'timestamp']
        read_only_fields = ['user', 'timestamp']