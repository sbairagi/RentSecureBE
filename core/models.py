from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords
from django.conf import settings

class User(AbstractUser):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    is_investor = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name

class App(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    history = HistoricalRecords(user_model=User)

    def __str__(self):
        return self.name

class UserApp(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_app')
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    access_granted = models.BooleanField(default=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    def __str__(self):
        return f"{self.user__name} - {self.app__name}"

class AILog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    prompt = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    def __str__(self):
        return f"{self.app__name} from {self.user__name} prompt : {self.prompt}"