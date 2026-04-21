from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AIAlert(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)