"""通知模块路由：/api/v1/notifications/"""
from django.urls import path

from apps.notifications.views import (
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationUnreadCountView,
)

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification_list"),
    # 静态路径提前，避免与数字参数混淆
    path(
        "notifications/unread_count/",
        NotificationUnreadCountView.as_view(),
        name="notification_unread_count",
    ),
    path(
        "notifications/read_all/",
        NotificationReadAllView.as_view(),
        name="notification_read_all",
    ),
    path(
        "notifications/<int:notification_id>/read/",
        NotificationReadView.as_view(),
        name="notification_read",
    ),
]