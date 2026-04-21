from django.db import models
from core.models import User
# Create your models here.


class SmartBotChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    reply = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class SmartBotMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)