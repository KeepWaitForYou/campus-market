"""通知模块模型：Notification（站内通知）。"""
from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    """通知类型。"""

    REVIEW = "review", "审核通知"
    ORDER = "order", "订单通知"
    FAVORITE = "favorite", "收藏通知"
    SYSTEM = "system", "系统通知"


class Notification(models.Model):
    """站内通知。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="接收用户",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField("标题", max_length=100)
    content = models.TextField("内容", blank=True, default="")
    type = models.CharField(
        "类型", max_length=20, choices=NotificationType.choices, default=NotificationType.SYSTEM
    )
    is_read = models.BooleanField("是否已读", default=False, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"], name="idx_notif_user_read"),
            models.Index(fields=["user", "-created_at"], name="idx_notif_user_created"),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.title}"