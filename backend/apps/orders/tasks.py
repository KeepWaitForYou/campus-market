"""订单模块 Celery 任务：超时自动取消、过期订单清扫。"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger("campus_market")


@shared_task(name="orders.order_timeout_cancel")
def order_timeout_cancel(order_id: int) -> None:
    """订单超时自动取消（创建订单 30 分钟后执行）。

    - 仅当订单仍为「待支付」时取消
    - 取消后恢复商品为「在售」
    """
    from apps.orders.models import Order, OrderStatus
    from apps.products.models import Product

    now = timezone.now()
    with transaction.atomic():
        updated = (
            Order.objects.filter(id=order_id, status=OrderStatus.PENDING)
            .select_for_update()
            .update(status=OrderStatus.CANCELLED, cancel_time=now)
        )
        if not updated:
            return  # 已被支付/取消，无需处理
        # 恢复商品（仅当被本次订单锁定的 off_shelf 状态）
        order = Order.objects.only("product_id", "order_no").get(id=order_id)
        Product.objects.filter(id=order.product_id, status=Product.OFF_SHELF).update(
            status=Product.ON_SALE, updated_at=now
        )
    _clear_home_cache()
    logger.info("Order %s auto cancelled due to timeout", order.order_no)
    # 通知买家
    from apps.orders.models import Order as OrderModel

    order = OrderModel.objects.only("buyer_id", "order_no").get(id=order_id)
    from apps.notifications.tasks import send_order_status

    send_order_status.delay(
        user_id=order.buyer_id,
        order_no=order.order_no,
        title="订单超时已取消",
        content=f"订单 {order.order_no} 超时未支付，已自动取消，商品已重新上架。",
        ntype="order",
    )


@shared_task(name="orders.sweep_expired_orders")
def sweep_expired_orders() -> int:
    """兜底清扫：Celery 延时任务丢失时，批量取消所有超时未支付订单（Beat 每 5 分钟触发）。"""
    from apps.orders.models import Order, OrderStatus

    deadline = timezone.now() - timedelta(seconds=settings.ORDER_TIMEOUT_SECONDS)
    expired_ids = list(
        Order.objects.filter(status=OrderStatus.PENDING, created_at__lt=deadline)
        .values_list("id", flat=True)
    )
    cancelled = 0
    for order_id in expired_ids:
        order_timeout_cancel.delay(order_id)
        cancelled += 1
    if cancelled:
        logger.info("Sweep expired orders: %d pending order(s) sent to cancel", cancelled)
    return cancelled


def _clear_home_cache() -> None:
    """失效首页商品列表缓存。"""
    from django.core.cache import cache

    cache.delete("products:home_list_v1")