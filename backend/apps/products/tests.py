"""商品模块测试：发布审核、列表搜索筛选、收藏、后台分类管理与统计。

运行方式（容器内）：
    docker compose exec backend python manage.py test apps.products
"""
from decimal import Decimal

from django.test import override_settings
from rest_framework import status as http_status
from rest_framework.test import APIClient, APITestCase

from apps.notifications.models import Notification
from apps.products.models import Category, Favorite, Product
from apps.users.models import User

PRODUCTS_URL = "/api/v1/products/"
CATEGORIES_URL = "/api/v1/categories/"
FAVORITES_URL = "/api/v1/favorites/"
ADMIN_PENDING_URL = "/api/v1/admin/products/pending/"
ADMIN_CATEGORIES_URL = "/api/v1/admin/categories/"
ADMIN_STATS_URL = "/api/v1/admin/stats/"


class ProductBaseTest(APITestCase):
    """公共 setUp：用户、管理员、分类。"""

    def setUp(self) -> None:
        self.seller = User.objects.create_user(username="seller", password="pass123456")
        self.buyer = User.objects.create_user(username="buyer", password="pass123456")
        self.admin = User.objects.create_superuser(username="root", password="Admin123456")
        self.category = Category.objects.create(name="电子产品", sort=1)
        self.client = APIClient()

    def create_product(self, status: str = Product.ON_SALE, **kw) -> Product:
        return Product.objects.create(
            seller=self.seller,
            category=self.category,
            title=kw.get("title", "二手笔记本电脑"),
            description=kw.get("description", "成色很好"),
            price=kw.get("price", "1999.00"),
            original_price=kw.get("original_price", "4999.00"),
            condition=kw.get("condition", "lightly_used"),
            campus=kw.get("campus", "主校区"),
            location=kw.get("location", "图书馆门口"),
            status=status,
        )


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ProductPublishTest(ProductBaseTest):
    """发布与审核。"""

    def test_publish_product_defaults_pending(self) -> None:
        self.client.force_authenticate(user=self.seller)
        resp = self.client.post(
            PRODUCTS_URL,
            {
                "category": self.category.id,
                "title": "小米手环",
                "description": "99 新",
                "price": "129.00",
                "condition": "like_new",
                "campus": "主校区",
                "location": "3 号宿舍",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, http_status.HTTP_201_CREATED)
        product = Product.objects.get(title="小米手环")
        self.assertEqual(product.status, Product.PENDING)

    def test_guest_cannot_publish(self) -> None:
        resp = self.client.post(
            PRODUCTS_URL,
            {"category": self.category.id, "title": "x", "price": "1.00"},
            format="json",
        )
        self.assertEqual(resp.status_code, http_status.HTTP_401_UNAUTHORIZED)

    def test_admin_approve_and_notify(self) -> None:
        product = self.create_product(status=Product.PENDING)
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(f"/api/v1/admin/products/{product.id}/approve/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.status, Product.ON_SALE)
        # 审核通过通知生成
        self.assertTrue(
            Notification.objects.filter(user=self.seller, type="review").exists()
        )

    def test_admin_reject_with_reason(self) -> None:
        product = self.create_product(status=Product.PENDING)
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            f"/api/v1/admin/products/{product.id}/reject/",
            {"reason": "图片不清晰"},
            format="json",
        )
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.status, Product.REJECTED)
        self.assertTrue(
            Notification.objects.filter(
                user=self.seller, type="review", content__contains="图片不清晰"
            ).exists()
        )

    def test_admin_forbid_off_shelf(self) -> None:
        product = self.create_product(status=Product.ON_SALE)
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(f"/api/v1/admin/products/{product.id}/forbid/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.status, Product.OFF_SHELF)
        self.assertTrue(
            Notification.objects.filter(user=self.seller, type="system").exists()
        )


class ProductListTest(ProductBaseTest):
    """列表只展示在售 + 搜索筛选。"""

    def test_list_only_on_sale(self) -> None:
        self.create_product(status=Product.ON_SALE, title="在售商品A")
        self.create_product(status=Product.PENDING, title="待审核商品B")
        self.create_product(status=Product.OFF_SHELF, title="已下架商品C")
        resp = self.client.get(PRODUCTS_URL)
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        titles = [item["title"] for item in resp.data["data"]["results"]]
        self.assertEqual(titles, ["在售商品A"])

    def test_search_and_price_filter(self) -> None:
        self.create_product(title="二手自行车", price="200.00")
        self.create_product(title="全新耳机", price="300.00")
        self.create_product(title="旧课本", price="15.00")
        # 关键词
        resp = self.client.get(PRODUCTS_URL, {"search": "自行车"})
        self.assertEqual(len(resp.data["data"]["results"]), 1)
        # 价格区间
        resp = self.client.get(PRODUCTS_URL, {"min_price": "100", "max_price": "250"})
        self.assertEqual(len(resp.data["data"]["results"]), 1)
        # 分类
        resp = self.client.get(PRODUCTS_URL, {"category": self.category.id})
        self.assertEqual(resp.data["data"]["count"], 3)


class FavoriteTest(ProductBaseTest):
    """收藏 / 取消收藏 / 我的收藏。"""

    def test_favorite_and_unfavorite(self) -> None:
        product = self.create_product()
        self.client.force_authenticate(user=self.buyer)
        # 收藏
        resp = self.client.post(f"{PRODUCTS_URL}{product.id}/favorite/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertTrue(Favorite.objects.filter(user=self.buyer, product=product).exists())
        # 列表
        resp = self.client.get(FAVORITES_URL)
        self.assertEqual(resp.data["data"]["count"], 1)
        # 取消收藏
        resp = self.client.delete(f"{PRODUCTS_URL}{product.id}/favorite/")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertFalse(Favorite.objects.filter(user=self.buyer, product=product).exists())


class AdminCategoryStatsTest(ProductBaseTest):
    """后台分类管理与数据统计。"""

    def test_admin_category_crud(self) -> None:
        self.client.force_authenticate(user=self.admin)
        # 新增
        resp = self.client.post(ADMIN_CATEGORIES_URL, {"name": "乐器", "sort": 9}, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_201_CREATED)
        new_cat = Category.objects.get(name="乐器")
        # 编辑 + 禁用
        resp = self.client.patch(
            f"{ADMIN_CATEGORIES_URL}{new_cat.id}",
            {"sort": 1, "is_active": False},
            format="json",
        )
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        new_cat.refresh_from_db()
        self.assertFalse(new_cat.is_active)
        self.assertEqual(new_cat.sort, 1)
        # 禁用后游客列表不可见
        resp = self.client.get(CATEGORIES_URL)
        names = [c["name"] for c in resp.data["data"]]
        self.assertNotIn("乐器", names)

    def test_admin_stats(self) -> None:
        self.create_product(status=Product.ON_SALE, price="100.00")
        self.create_product(status=Product.ON_SALE, price="50.00")
        self.create_product(status=Product.PENDING)
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(ADMIN_STATS_URL)
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        data = resp.data["data"]
        self.assertEqual(data["total_products"], 3)
        self.assertEqual(data["pending_products"], 1)