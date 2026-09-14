"""通知模块序列化器。"""
from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """通知展示。"""

    type_label = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = ("id", "title", "content", "type", "type_label", "is_read", "created_at")