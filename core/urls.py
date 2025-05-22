from django.urls import path
from .views import RegisterView, LoginView, AppListView, AILogListCreateView, ChangePasswordView, ResetPasswordView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    # comman auth end-points
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),


    # 
    path("apps/", AppListView.as_view(), name="apps-list"),
    path("logs/", AILogListCreateView.as_view(), name="ai-logs"),
]