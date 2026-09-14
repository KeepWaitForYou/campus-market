"""订单模块模型：Order（含订单状态机）。"""
import random

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_order_no() -> str:
    """生成订单号：CM + 年月日时分秒 + 4 位随机数，如 CM202609141530121234。"""
    now = timezone.localtime()
    return f"CM{now:%Y%m%d%H%M%S}{random.randint(1000, 9999)}"


class OrderStatus(models.TextChoices):
    """订单状态机。

    流转：
        pending(待支付) -> paid(已支付) -> shipped(已发货) -> completed(已完成)
        pending(待支付) -> cancelled(已取消)
    completed / cancelled 为终态，不允许再变更。
    """

    PENDING = "pending", "待支付"
    PAID = "paid", "已支付"
    SHIPPED = "shipped", "已发货"
    COMPLETED = "completed", "已完成"
    CANCELLED = "cancelled", "已取消"


# 非终态集合（存在订单时商品会被锁定）。
# 注意：Python 3.11 的 enum 机制不允许枚举类体内包含成员对象的类属性，
# 故作为模块级常量定义在类外。
ORDER_ACTIVE_STATUSES = (OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.SHIPPED)


class Order(models.Model):
    """二手交易订单。

    商品锁定约定：
    - 下单成功（pending）：商品状态 on_sale -> off_shelf（防止被重复下单）
    - 支付成功（paid）：商品状态 off_shelf -> sold（已售出）
    - 取消订单（cancelled）：商品状态 off_shelf -> on_sale（重新上架）
    """

    order_no = models.CharField("订单号", max_length=32, unique=True, db_index=True)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="买家",
        on_delete=models.PROTECT,
        related_name="bought_orders",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="卖家",
        on_delete=models.PROTECT,
        related_name="sold_orders",
    )
    product = models.ForeignKey(
        "products.Product",
        verbose_name="商品",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    amount = models.DecimalField("成交金额", max_digits=10, decimal_places=2)
    status = models.CharField(
        "状态", max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True
    )
    remark = models.CharField("买家备注", max_length=200, blank=True, default="")
    pay_time = models.DateTimeField("支付时间", null=True, blank=True)
    ship_time = models.DateTimeField("发货时间", null=True, blank=True)
    finish_time = models.DateTimeField("完成时间", null=True, blank=True)
    cancel_time = models.DateTimeField("取消时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["buyer", "-created_at"], name="idx_order_buyer_created"),
            models.Index(fields=["seller", "-created_at"], name="idx_order_seller_created"),
            models.Index(fields=["product", "status"], name="idx_order_product_status"),
        ]

    def __str__(self) -> str:
        return f"{self.order_no}({self.get_status_display()})"

    def save(self, *args, **kwargs) -> None:
        """首次保存时自动生成订单号。"""
        if not self.order_no:
            self.order_no = generate_order_no()
        super().save(*args, **kwargs)