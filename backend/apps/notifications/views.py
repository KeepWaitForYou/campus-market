"""通知模块视图：列表、未读数、标记已读、全部已读。"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.response import fail, ok
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """GET /api/v1/notifications/ 我的通知列表（?is_read=0 只看未读，分页）。"""

    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        is_read = (self.request.query_params.get("is_read") or "").strip()
        if is_read in ("0", "1"):
            qs = qs.filter(is_read=(is_read == "1"))
        return qs


class NotificationUnreadCountView(APIView):
    """GET /api/v1/notifications/unread_count/ 未读通知数（导航栏角标用）。"""

    def get(self, request) -> Response:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return ok({"unread_count": count})


class NotificationReadView(APIView):
    """POST /api/v1/notifications/{id}/read/ 标记某条通知已读（幂等，仅本人）。"""

    def post(self, request, notification_id: int) -> Response:
        Notification.objects.filter(
            id=notification_id, user=request.user, is_read=False
        ).update(is_read=True)
        if not Notification.objects.filter(id=notification_id, user=request.user).exists():
            return fail("通知不存在", status=status.HTTP_404_NOT_FOUND)
        return ok({"id": notification_id, "is_read": True}, "已标记已读")


class NotificationReadAllView(APIView):
    """POST /api/v1/notifications/read_all/ 一键全部已读。"""

    def post(self, request) -> Response:
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return ok({"marked": count}, "已全部标记已读")