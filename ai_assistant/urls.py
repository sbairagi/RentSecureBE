# urls.py

from django.urls import path
from .views import whatsapp_webhook

urlpatterns = [
    path("webhooks/whatsapp/", whatsapp_webhook, name="whatsapp_webhook")
]



