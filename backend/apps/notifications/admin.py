"""通知后台管理：Django admin 注册。"""
from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "type", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("user__username", "title")
    readonly_fields = ("created_at",)