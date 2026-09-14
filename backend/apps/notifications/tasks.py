"""通知模块 Celery 任务：审核结果、订单状态、收藏商品被下单、系统通知。"""
import logging

from celery import shared_task

logger = logging.getLogger("campus_market")


@shared_task(name="notifications.send_system_notification")
def send_system_notification(user_id: int, title: str, content: str) -> None:
    """通用系统通知（如商品被管理员下架）。"""
    from apps.notifications.models import Notification, NotificationType

    Notification.objects.create(
        user_id=user_id, title=title, content=content, type=NotificationType.SYSTEM
    )


@shared_task(name="notifications.send_review_result")
def send_review_result(user_id: int, product_id: int, passed: bool, reason: str = "") -> None:
    """商品审核结果通知（通过 / 不通过含原因）。"""
    from apps.notifications.models import Notification, NotificationType
    from apps.products.models import Product

    try:
        product = Product.objects.only("title").get(id=product_id)
    except Product.DoesNotExist:
        logger.warning("Notification: product %s not found", product_id)
        return
    if passed:
        title = "商品审核通过"
        content = f"您发布的商品「{product.title}」已审核通过，现已在售，快去看看吧。"
        ntype = NotificationType.REVIEW
    else:
        title = "商品审核未通过"
        content = f"您发布的商品「{product.title}」未通过审核，原因：{reason or '未说明'}。" \
                  "请修改后重新发布。"
        ntype = NotificationType.REVIEW
    Notification.objects.create(user_id=user_id, title=title, content=content, type=ntype)


@shared_task(name="notifications.send_order_status")
def send_order_status(
    user_id: int, order_no: str, title: str, content: str, ntype: str = "order"
) -> None:
    """订单状态变更通知（支付/发货/确认/超时取消等）。"""
    from apps.notifications.models import Notification, NotificationType

    Notification.objects.create(
        user_id=user_id, title=title, content=content, type=NotificationType(ntype)
    )


@shared_task(name="notifications.notify_favorites_ordered")
def notify_favorites_ordered(product_id: int, buyer_id: int) -> None:
    """收藏的商品被下单通知：提醒所有收藏者（买家除外）。"""
    from apps.notifications.models import Notification, NotificationType
    from apps.products.models import Favorite, Product

    try:
        product = Product.objects.only("title").get(id=product_id)
    except Product.DoesNotExist:
        return
    user_ids = list(
        Favorite.objects.filter(product_id=product_id)
        .exclude(user_id=buyer_id)
        .values_list("user_id", flat=True)
    )
    if not user_ids:
        return
    notifications = [
        Notification(
            user_id=uid,
            title="收藏的商品已被下单",
            content=f"您收藏的商品「{product.title}」已被其他用户下单，喜欢的宝贝手慢无哦～",
            type=NotificationType.FAVORITE,
        )
        for uid in user_ids
    ]
    Notification.objects.bulk_create(notifications)
    logger.info("Notify %d followers for product %s", len(user_ids), product_id)