from django.urls import path
from wealth_concierge_platform.management import views

urlpatterns = [
    path('register-fcm/', views.register_fcm_token, name='register-fcm'),
]