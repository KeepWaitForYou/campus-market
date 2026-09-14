"""用户模型：基于 Django AbstractUser 扩展校园用户字段。"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """校园用户。

    扩展字段：
    - nickname     昵称（前台展示名）
    - phone        手机号
    - avatar       头像（Pillow 压缩后存储，Nginx 代理 /media/）
    - student_no   学号
    - is_verified  是否已实名认证（预留，本期仅展示用途）
    """

    nickname = models.CharField("昵称", max_length=50, blank=True, default="")
    phone = models.CharField("手机号", max_length=20, blank=True, default="")
    avatar = models.ImageField("头像", upload_to="avatars/%Y/%m/", blank=True, null=True)
    student_no = models.CharField("学号", max_length=30, blank=True, default="")
    is_verified = models.BooleanField("是否已认证", default=False)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.username

    @property
    def display_name(self) -> str:
        """前台展示名：优先昵称，其次用户名。"""
        return self.nickname or self.username