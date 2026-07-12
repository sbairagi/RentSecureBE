from django.urls import path

from .views import (
    get_notifications,
    mark_notification_read,
    register_fcm_token,
    save_device_token,
)

urlpatterns = [
    path("register-fcm/", register_fcm_token, name="register-fcm"),
    path("get/", get_notifications, name="get-notifications"),
    path(
        "mark/<int:notification_id>/",
        mark_notification_read,
        name="mark-notification-read",
    ),
    path("save-token/", save_device_token, name="save-device-token"),
]
