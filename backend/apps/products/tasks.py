"""商品模块 Celery 任务：图片压缩、统计更新。"""
import logging

from celery import shared_task

logger = logging.getLogger("campus_market")


@shared_task(name="products.compress_image")
def compress_image_task(image_id: int) -> None:
    """
    使用 Pillow 压缩商品图片并覆盖原文件。

    - 超过 1200px 的最长边等比缩小
    - 统一转成 JPEG，quality=85
    - 失败仅记录日志，不影响主流程
    """
    from PIL import Image, UnidentifiedImageError

    from apps.products.models import ProductImage

    from django.core.files.storage import default_storage

    try:
        img_obj = ProductImage.objects.select_related("product").get(id=image_id)
    except ProductImage.DoesNotExist:
        return

    path = img_obj.image.name
    if not default_storage.exists(path):
        return

    full_path = img_obj.image.path
    try:
        with Image.open(full_path) as img:
            img = img.convert("RGB")
            img.thumbnail((1200, 1200), Image.LANCZOS)
            img.save(full_path, "JPEG", quality=85, optimize=True)
        logger.info("Compressed image %s", path)
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("Compress image failed %s: %s", path, exc)


@shared_task(name="products.refresh_hot_keyword")
def record_search_keyword(keyword: str) -> None:
    """将搜索关键词写入 Redis Sorted Set（热度 +1），保留 Top 20。"""
    from django_redis import get_redis_connection

    keyword = keyword.strip()
    if not keyword:
        return
    conn = get_redis_connection("default")
    key = "products:hot_searches"
    conn.zincrby(key, 1, keyword)
    conn.zremrangebyrank(key, 0, -21)  # 只保留前 20 个
    conn.expire(key, 3600 * 24)


@shared_task(name="products.increment_view")
def increment_view_count(product_id: int) -> None:
    """异步增加商品浏览量。"""
    from django.db.models import F

    from apps.products.models import Product

    Product.objects.filter(id=product_id).update(view_count=F("view_count") + 1)