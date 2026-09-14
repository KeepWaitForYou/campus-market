"""订单模块测试：下单锁定、支付、发货、确认、取消、超时取消、并发防护。

运行方式（容器内）：
    docker compose exec backend python manage.py test apps.orders
"""
from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.test import APIClient, APITestCase

from apps.orders.models import Order, OrderStatus
from apps.orders.tasks import sweep_expired_orders
from apps.products.models import Category, Product, ProductStatus
from apps.users.models import User

ORDERS_URL = "/api/v1/orders/"


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OrderFlowTest(APITestCase):
    """订单完整生命周期与状态机。"""

    def setUp(self) -> None:
        self.buyer = User.objects.create_user(username="buyer", password="pass123456")
        self.seller = User.objects.create_user(username="seller", password="pass123456")
        self.category = Category.objects.create(name="书籍教材", sort=1)
        self.product: Product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            title="高数教材",
            description="九成新",
            price="35.00",
            condition="like_new",
            campus="主校区",
            status=ProductStatus.ON_SALE,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.buyer)

    def create_order(self) -> Order:
        resp = self.client.post(ORDERS_URL, {"product": self.product.id}, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_201_CREATED)
        return Order.objects.get(order_no=resp.data["data"]["order_no"])

    def test_create_order_locks_product(self) -> None:
        order = self.create_order()
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.product.refresh_from_db()
        # 下单后商品被锁定（off_shelf），防止重复购买
        self.assertEqual(self.product.status, ProductStatus.OFF_SHELF)

    def test_duplicate_order_conflict(self) -> None:
        self.create_order()
        resp = self.client.post(ORDERS_URL, {"product": self.product.id}, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_409_CONFLICT)

    def test_cannot_buy_own_product(self) -> None:
        self.client.force_authenticate(user=self.seller)
        resp = self.client.post(ORDERS_URL, {"product": self.product.id}, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_400_BAD_REQUEST)

    def test_full_flow_pay_ship_confirm(self) -> None:
        order = self.create_order()
        # 支付（买家）
        resp = self.client.post(f"{ORDERS_URL}{order.id}/pay/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.PAID)
        self.assertIsNotNone(order.pay_time)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, ProductStatus.SOLD)  # 支付后已售出

        # 发货（卖家）
        self.client.force_authenticate(user=self.seller)
        resp = self.client.post(f"{ORDERS_URL}{order.id}/ship/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.SHIPPED)

        # 确认收货（买家）
        self.client.force_authenticate(user=self.buyer)
        resp = self.client.post(f"{ORDERS_URL}{order.id}/confirm/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.COMPLETED)
        self.assertIsNotNone(order.finish_time)

        # 终态不可再变更
        resp = self.client.post(f"{ORDERS_URL}{order.id}/confirm/")
        self.assertEqual(resp.status_code, http_status.HTTP_400_BAD_REQUEST)

    def test_terminal_status_immutable(self) -> None:
        order = self.create_order()
        resp = self.client.post(f"{ORDERS_URL}{order.id}/cancel/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        # 已取消的订单不能再支付
        resp = self.client.post(f"{ORDERS_URL}{order.id}/pay/")
        self.assertEqual(resp.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, ProductStatus.ON_SALE)

    def test_unrelated_user_cannot_operate(self) -> None:
        order = self.create_order()
        stranger = User.objects.create_user(username="stranger", password="pass123456")
        self.client.force_authenticate(user=stranger)
        resp = self.client.post(f"{ORDERS_URL}{order.id}/pay/")
        self.assertEqual(resp.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_order_list_role_filter(self) -> None:
        order = self.create_order()
        # 买家视角：bought
        resp = self.client.get(ORDERS_URL, {"role": "bought"})
        self.assertEqual(resp.data["data"]["count"], 1)
        self.assertEqual(resp.data["data"]["results"][0]["role"], "bought")
        # 卖家视角：sold
        self.client.force_authenticate(user=self.seller)
        resp = self.client.get(ORDERS_URL, {"role": "sold"})
        self.assertEqual(resp.data["data"]["count"], 1)
        self.assertEqual(resp.data["data"]["results"][0]["id"], order.id)

    def test_timeout_auto_cancel(self) -> None:
        """模拟订单超时：把创建时间改到 30 分钟前，触发清扫任务。"""
        order = self.create_order()
        past = timezone.now() - timedelta(minutes=31)
        Order.objects.filter(id=order.id).update(created_at=past)
        # 直接执行兜底清扫（内部 delay 在 eager 模式下同步执行超时取消）
        sweep_expired_orders()
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELLED)
        self.assertIsNotNone(order.cancel_time)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, ProductStatus.ON_SALE)