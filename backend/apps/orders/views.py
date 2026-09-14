"""订单模块视图：创建 / 列表 / 详情 / 支付 / 取消 / 发货 / 确认收货。"""
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.response import fail, ok
from apps.orders.models import ORDER_ACTIVE_STATUSES, Order, OrderStatus
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
)
from apps.orders.tasks import order_timeout_cancel
from apps.products.models import Product
from apps.notifications.tasks import notify_favorites_ordered, send_order_status


class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/orders/                 我的订单（?role=bought|sold，默认 bought，支持 ?status= 筛选）
    POST /api/v1/orders/                 创建订单（选择商品，锁定商品，30 分钟未支付自动取消）
    """

    permission_classes = []

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated

        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = (
            Order.objects.select_related("product", "buyer", "seller")
            .prefetch_related("product__images")
        )
        # 管理员可查看全部订单；普通用户按角色过滤
        if not user.is_staff:
            role = self.request.query_params.get("role", "bought")
            if role == "sold":
                qs = qs.filter(seller=user)
            else:
                qs = qs.filter(buyer=user)
        # 状态筛选
        s = (self.request.query_params.get("status") or "").strip()
        if s:
            qs = qs.filter(status=s)
        return qs.order_by("-created_at")

    # ---------------- 创建订单 ----------------
    def create(self, request, *args, **kwargs) -> Response:
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        remark = serializer.validated_data.get("remark", "")

        if product.status != Product.ON_SALE:
            return fail("商品当前不可购买")
        if product.seller_id == request.user.id:
            return fail("不能购买自己发布的商品")
        if Order.objects.filter(
            product=product, status__in=ORDER_ACTIVE_STATUSES
        ).exists():
            return fail("该商品已有进行中的订单")

        # 原子锁定商品：on_sale -> off_shelf，防止并发重复下单
        with transaction.atomic():
            locked = Product.objects.filter(id=product.id, status=Product.ON_SALE).update(
                status=Product.OFF_SHELF, updated_at=timezone.now()
            )
            if not locked:
                return fail("手慢了，商品已被其他人下单", status=status.HTTP_409_CONFLICT)
            order = Order.objects.create(
                buyer=request.user,
                seller=product.seller,
                product=product,
                amount=product.price,
                remark=remark[:200],
            )

        # 延时任务：默认 30 分钟未支付自动取消
        order_timeout_cancel.apply_async(
            args=[order.id], countdown=self._timeout_seconds()
        )
        # 通知商品的收藏者（买家本人除外）
        notify_favorites_ordered.delay(product.id, request.user.id)
        cache.delete("products:home_list_v1")

        data = OrderDetailSerializer(order, context={"request": request}).data
        return ok(
            data,
            message=f"下单成功，请在 {self._timeout_seconds() // 60} 分钟内完成支付",
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _timeout_seconds() -> int:
        from django.conf import settings

        return settings.ORDER_TIMEOUT_SECONDS


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/v1/orders/{id}/ 订单详情（买家 / 卖家 / 管理员可见）。"""

    serializer_class = OrderDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(Q(buyer=user) | Q(seller=user))

    def retrieve(self, request, *args, **kwargs) -> Response:
        instance = self.get_object()
        return ok(self.get_serializer(instance).data)


def _get_order_for_user(request, order_id: int, role: str) -> tuple[Order | None, Response | None]:
    """按角色取订单，返回 (order, error_response)。"""
    try:
        order = Order.objects.select_related("product", "buyer", "seller").get(id=order_id)
    except Order.DoesNotExist:
        return None, fail("订单不存在", status=status.HTTP_404_NOT_FOUND)
    user = request.user
    is_admin = user.is_staff
    if role == "buyer" and order.buyer_id != user.id and not is_admin:
        return None, fail("无权操作该订单", status=status.HTTP_403_FORBIDDEN)
    if role == "seller" and order.seller_id != user.id and not is_admin:
        return None, fail("无权操作该订单", status=status.HTTP_403_FORBIDDEN)
    return order, None


class OrderPayView(APIView):
    """POST /api/v1/orders/{id}/pay/ 模拟支付：待支付 -> 已支付，商品标记已售出。"""

    def post(self, request, order_id: int) -> Response:
        order, err = _get_order_for_user(request, order_id, role="buyer")
        if err:
            return err
        now = timezone.now()
        with transaction.atomic():
            updated = Order.objects.filter(id=order.id, status=OrderStatus.PENDING).update(
                status=OrderStatus.PAID, pay_time=now
            )
            if not updated:
                return fail("订单状态不允许支付")
            # 商品已售出（锁定状态 off_shelf -> sold）
            Product.objects.filter(id=order.product_id, status=Product.OFF_SHELF).update(
                status=Product.SOLD, updated_at=now
            )
        order.refresh_from_db()
        cache.delete("products:home_list_v1")
        # 通知卖家
        send_order_status.delay(
            user_id=order.seller_id,
            order_no=order.order_no,
            title="订单已支付",
            content=f"买家已支付订单 {order.order_no}，请尽快发货。",
            ntype="order",
        )
        return ok(OrderDetailSerializer(order, context={"request": request}).data, "支付成功")


class OrderCancelView(APIView):
    """POST /api/v1/orders/{id}/cancel/ 取消订单（仅待支付），商品重新上架。"""

    def post(self, request, order_id: int) -> Response:
        order, err = _get_order_for_user(request, order_id, role="buyer")
        if err:
            return err
        now = timezone.now()
        with transaction.atomic():
            updated = Order.objects.filter(id=order.id, status=OrderStatus.PENDING).update(
                status=OrderStatus.CANCELLED, cancel_time=now
            )
            if not updated:
                return fail("当前状态不可取消")
            # 恢复商品在售
            Product.objects.filter(id=order.product_id, status=Product.OFF_SHELF).update(
                status=Product.ON_SALE, updated_at=now
            )
        order.refresh_from_db()
        cache.delete("products:home_list_v1")
        return ok(OrderDetailSerializer(order, context={"request": request}).data, "订单已取消")


class OrderShipView(APIView):
    """POST /api/v1/orders/{id}/ship/ 卖家发货：已支付 -> 已发货。"""

    def post(self, request, order_id: int) -> Response:
        order, err = _get_order_for_user(request, order_id, role="seller")
        if err:
            return err
        now = timezone.now()
        updated = Order.objects.filter(id=order.id, status=OrderStatus.PAID).update(
            status=OrderStatus.SHIPPED, ship_time=now
        )
        if not updated:
            return fail("当前状态不可发货")
        order.refresh_from_db()
        # 通知买家
        send_order_status.delay(
            user_id=order.buyer_id,
            order_no=order.order_no,
            title="订单已发货",
            content=f"卖家已发货，订单号 {order.order_no}，请留意收货并在收到后确认收货。",
            ntype="order",
        )
        return ok(OrderDetailSerializer(order, context={"request": request}).data, "已发货")


class OrderConfirmView(APIView):
    """POST /api/v1/orders/{id}/confirm/ 买家确认收货：已发货 -> 已完成。"""

    def post(self, request, order_id: int) -> Response:
        order, err = _get_order_for_user(request, order_id, role="buyer")
        if err:
            return err
        now = timezone.now()
        updated = Order.objects.filter(id=order.id, status=OrderStatus.SHIPPED).update(
            status=OrderStatus.COMPLETED, finish_time=now
        )
        if not updated:
            return fail("当前状态不可确认收货")
        order.refresh_from_db()
        # 通知卖家
        send_order_status.delay(
            user_id=order.seller_id,
            order_no=order.order_no,
            title="订单已完成",
            content=f"买家已确认收货，订单 {order.order_no} 完成，交易款项已结算。",
            ntype="order",
        )
        return ok(OrderDetailSerializer(order, context={"request": request}).data, "交易完成")