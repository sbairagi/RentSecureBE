from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    is_investor = models.BooleanField(default=False)

class App(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

class UserApp(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    access_granted = models.BooleanField(default=True)

class AILog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    prompt = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)