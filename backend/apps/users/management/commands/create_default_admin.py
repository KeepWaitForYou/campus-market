"""创建默认管理员：python manage.py create_default_admin

默认账号 admin / Admin123456（可通过环境变量 DJANGO_ADMIN_USERNAME / DJANGO_ADMIN_PASSWORD 覆盖），
已存在则跳过，幂等。
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "创建默认管理员账号（admin / Admin123456）"

    def handle(self, *args, **options) -> None:
        User = get_user_model()
        username = os.getenv("DJANGO_ADMIN_USERNAME", "admin")
        password = os.getenv("DJANGO_ADMIN_PASSWORD", "Admin123456")

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"管理员 {username} 已存在，跳过创建"))
            return

        User.objects.create_superuser(
            username=username,
            password=password,
            email="admin@campus.local",
            nickname="超级管理员",
        )
        self.stdout.write(
            self.style.SUCCESS(f"默认管理员创建成功：{username} / {password}（请登录后尽快修改密码）")
        )