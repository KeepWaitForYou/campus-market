"""初始化商品分类：python manage.py init_categories

按名称幂等插入默认分类，已存在的分类不会被重复创建或修改。
"""
from django.core.management.base import BaseCommand

from apps.products.models import Category

DEFAULT_CATEGORIES = [
    ("书籍教材", 1),
    ("电子产品", 2),
    ("生活用品", 3),
    ("服饰鞋包", 4),
    ("运动户外", 5),
    ("美妆个护", 6),
    ("校园卡券", 7),
    ("其他闲置", 8),
]


class Command(BaseCommand):
    help = "初始化默认商品分类（幂等）"

    def handle(self, *args, **options) -> None:
        exists_names = set(Category.objects.filter(
            name__in=[name for name, _ in DEFAULT_CATEGORIES]
        ).values_list("name", flat=True))

        created = 0
        for name, sort in DEFAULT_CATEGORIES:
            if name in exists_names:
                continue
            Category.objects.create(name=name, sort=sort, is_active=True)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"分类初始化完成：新增 {created} 个，已存在 {len(exists_names)} 个")
        )