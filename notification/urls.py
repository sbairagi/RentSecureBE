from django.urls import path

from .views import (
    delete_notification,
    get_notifications,
    list_devices,
    mark_all_notifications_read,
    mark_notification_read,
    notification_preferences,
    notification_types,
    register_fcm_token,
    save_device_token,
    unread_count,
    unregister_device,
)

urlpatterns = [
    path("register-fcm/", register_fcm_token, name="register-fcm"),
    path("get/", get_notifications, name="notification-list"),
    path("unread-count/", unread_count, name="unread-count"),
    path("mark-all-read/", mark_all_notifications_read, name="mark-all-read"),
    path(
        "mark/<int:notification_id>/",
        mark_notification_read,
        name="mark-notification-read",
    ),
    path(
        "<int:notification_id>/",
        delete_notification,
        name="delete-notification",
    ),
    path("save-token/", save_device_token, name="save-device-token"),
    path("devices/", list_devices, name="device-list"),
    path(
        "devices/<int:device_id>/",
        unregister_device,
        name="device-unregister",
    ),
    path("preferences/", notification_preferences, name="notification-preferences"),
    path("types/", notification_types, name="notification-types"),
]
