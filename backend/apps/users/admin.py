"""Django Admin 注册用户模型。"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """用户后台管理：支持按状态筛选与禁用/启用。"""

    list_display = (
        "id",
        "username",
        "nickname",
        "phone",
        "email",
        "student_no",
        "is_verified",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_verified", "date_joined")
    search_fields = ("username", "nickname", "phone", "email", "student_no")
    ordering = ("-date_joined",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("校园信息", {"fields": ("nickname", "phone", "student_no", "avatar", "is_verified")}),
    )