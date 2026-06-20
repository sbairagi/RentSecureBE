from django.conf import settings
from django.db import models


class SmartBotChat(models.Model):
    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    message: str = models.TextField()
    reply: str = models.TextField()
    timestamp: "models.DateTimeField" = models.DateTimeField(auto_now_add=True)


class SmartBotMessage(models.Model):
    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    query: str = models.TextField()
    response: str = models.TextField()
    created_at: "models.DateTimeField" = models.DateTimeField(auto_now_add=True)


class AIAlert(models.Model):
    owner: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    alert_type: str = models.CharField(max_length=100)
    message: str = models.TextField()
    created_at: "models.DateTimeField" = models.DateTimeField(auto_now_add=True)
    resolved: bool = models.BooleanField(default=False)
