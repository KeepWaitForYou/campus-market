"""通知模块测试：审核通知、订单通知、收藏被下单通知、已读标记。

运行方式（容器内）：
    docker compose exec backend python manage.py test apps.notifications
"""
from django.test import override_settings
from rest_framework import status as http_status
from rest_framework.test import APIClient, APITestCase

from apps.notifications.models import Notification
from apps.notifications.tasks import send_review_result, send_system_notification
from apps.products.models import Category, Favorite, Product, ProductStatus
from apps.users.models import User

NOTIFICATIONS_URL = "/api/v1/notifications/"
UNREAD_URL = "/api/v1/notifications/unread_count/"
ORDERS_URL = "/api/v1/orders/"
PRODUCTS_URL = "/api/v1/products/"


class NotificationTaskTest(APITestCase):
    """任务函数直接产生的通知。"""

    def test_send_review_result(self) -> None:
        seller = User.objects.create_user(username="seller", password="pass123456")
        category = Category.objects.create(name="其他闲置", sort=8)
        product = Product.objects.create(
            seller=seller, category=category, title="台灯", price="20.00", status=ProductStatus.PENDING
        )
        send_review_result(user_id=seller.id, product_id=product.id, passed=True, reason="")
        send_review_result(user_id=seller.id, product_id=product.id, passed=False, reason="照片模糊")
        notes = Notification.objects.filter(user=seller, type="review").order_by("id")
        self.assertEqual(notes.count(), 2)
        self.assertIn("已审核通过", notes[0].content)
        self.assertIn("照片模糊", notes[1].content)

    def test_send_system_notification(self) -> None:
        user = User.objects.create_user(username="u1", password="pass123456")
        send_system_notification(user_id=user.id, title="系统升级", content="今晚 2 点维护")
        note = Notification.objects.get(user=user)
        self.assertEqual(note.type, "system")
        self.assertFalse(note.is_read)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class NotificationFlowTest(APITestCase):
    """通过 API 链路触发的通知。"""

    def setUp(self) -> None:
        self.buyer = User.objects.create_user(username="buyer", password="pass123456")
        self.seller = User.objects.create_user(username="seller", password="pass123456")
        self.fan = User.objects.create_user(username="fan", password="pass123456")
        self.category = Category.objects.create(name="电子产品", sort=1)
        self.product: Product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            title="蓝牙耳机",
            price="99.00",
            status=ProductStatus.ON_SALE,
        )
        self.client = APIClient()

    def test_favorite_ordered_notifies_followers(self) -> None:
        # 收藏者收藏商品
        self.client.force_authenticate(user=self.fan)
        self.client.post(f"{PRODUCTS_URL}{self.product.id}/favorite/")
        # 买家下单
        self.client.force_authenticate(user=self.buyer)
        resp = self.client.post(ORDERS_URL, {"product": self.product.id}, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_201_CREATED)
        # 收藏者（买家除外）收到收藏通知
        self.assertTrue(
            Notification.objects.filter(user=self.fan, type="favorite").exists()
        )
        # 买家本人不应收到收藏通知
        self.assertFalse(
            Notification.objects.filter(user=self.buyer, type="favorite").exists()
        )

    def test_order_status_notifies_seller(self) -> None:
        self.client.force_authenticate(user=self.buyer)
        order_resp = self.client.post(ORDERS_URL, {"product": self.product.id}, format="json")
        order_id = order_resp.data["data"]["id"]
        self.client.post(f"{ORDERS_URL}{order_id}/pay/")
        # 卖家收到"订单已支付"通知
        self.assertTrue(
            Notification.objects.filter(user=self.seller, type="order").exists()
        )

    def test_list_mark_read_unread_count(self) -> None:
        user = self.seller
        Notification.objects.create(user=user, title="第一条", content="c1", type="system")
        Notification.objects.create(user=user, title="第二条", content="c2", type="system")
        self.client.force_authenticate(user=user)

        # 未读计数
        resp = self.client.get(UNREAD_URL)
        self.assertEqual(resp.data["data"]["unread_count"], 2)

        # 列表
        resp = self.client.get(NOTIFICATIONS_URL)
        self.assertEqual(resp.data["data"]["count"], 2)

        # 标记已读
        first_id = resp.data["data"]["results"][0]["id"]
        resp = self.client.post(f"{NOTIFICATIONS_URL}{first_id}/read/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        first = Notification.objects.get(id=first_id)
        self.assertTrue(first.is_read)

        # 幂等：重复标记
        resp = self.client.post(f"{NOTIFICATIONS_URL}{first_id}/read/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)

        # 未读数减一
        resp = self.client.get(UNREAD_URL)
        self.assertEqual(resp.data["data"]["unread_count"], 1)

        # 全部已读
        resp = self.client.post(f"{NOTIFICATIONS_URL}read_all/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertEqual(Notification.objects.filter(user=user, is_read=False).count(), 0)