"""商品后台管理视图：审核（待审核列表 / 通过 / 拒绝）、分类管理、违规下架、数据统计。"""
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.response import fail, ok
from apps.products.models import Category, Product
from apps.products.serializers import CategorySerializer, ProductListSerializer


class PendingProductListView(generics.ListAPIView):
    """GET /api/v1/admin/products/pending/ 待审核商品列表。"""

    permission_classes = [IsAdminUser]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return (
            Product.objects.filter(status=Product.PENDING)
            .select_related("seller", "category")
            .prefetch_related("images")
            .order_by("created_at")
        )


class ApproveProductView(APIView):
    """POST /api/v1/admin/products/{id}/approve/ 审核通过 -> 在售。"""

    permission_classes = [IsAdminUser]

    def post(self, request, product_id: int) -> Response:
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return fail("商品不存在", status=status.HTTP_404_NOT_FOUND)
        if product.status != Product.PENDING:
            return fail("仅待审核商品可执行此操作")
        product.status = Product.ON_SALE
        product.save(update_fields=["status", "updated_at"])
        cache.delete("products:home_list_v1")
        # 通知卖家（延迟导入避免循环依赖）
        from apps.notifications.tasks import send_review_result

        send_review_result.delay(
            user_id=product.seller_id, product_id=product.id, passed=True, reason=""
        )
        return ok(message="审核通过，商品已上架")


class RejectProductView(APIView):
    """POST /api/v1/admin/products/{id}/reject/ 审核不通过（需填写原因，发布者将收到通知）。"""

    permission_classes = [IsAdminUser]

    def post(self, request, product_id: int) -> Response:
        reason = (request.data.get("reason") or "").strip()
        if not reason:
            return fail("请填写驳回原因")
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return fail("商品不存在", status=status.HTTP_404_NOT_FOUND)
        if product.status != Product.PENDING:
            return fail("仅待审核商品可执行此操作")
        product.status = Product.REJECTED
        product.reject_reason = reason[:255]
        product.save(update_fields=["status", "reject_reason", "updated_at"])
        cache.delete("products:home_list_v1")
        from apps.notifications.tasks import send_review_result

        send_review_result.delay(
            user_id=product.seller_id, product_id=product.id, passed=False, reason=reason
        )
        return ok(message="已驳回该商品")


# ---------------- 分类管理 ----------------
class CategoryAdminListView(generics.ListCreateAPIView):
    """GET/POST /api/v1/admin/categories/ 分类列表（含禁用）与新增。

    公开的 GET /api/v1/categories/ 只返回启用分类；
    管理后台需要看到已禁用分类用于启停管理，故提供本接口。
    """

    permission_classes = [IsAdminUser]
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.all().order_by("sort", "id")

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(serializer.data, "分类已创建", status=status.HTTP_201_CREATED)


class CategoryAdminDetailView(APIView):
    """PATCH /api/v1/admin/categories/{id}/ 编辑分类（名称 / 排序 / 启用状态）。"""

    permission_classes = [IsAdminUser]

    def patch(self, request, category_id: int) -> Response:
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return fail("分类不存在", status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(serializer.data, "分类已更新")


# ---------------- 违规下架 ----------------
class ForbidProductView(APIView):
    """POST /api/v1/admin/products/{id}/forbid/ 违规商品强制下架（通知卖家）。"""

    permission_classes = [IsAdminUser]

    def post(self, request, product_id: int) -> Response:
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return fail("商品不存在", status=status.HTTP_404_NOT_FOUND)
        if product.status not in (Product.ON_SALE, Product.PENDING):
            return fail("仅待审核或在售商品可下架")
        product.status = Product.OFF_SHELF
        product.save(update_fields=["status", "updated_at"])
        cache.delete("products:home_list_v1")
        from apps.notifications.tasks import send_system_notification

        send_system_notification.delay(
            user_id=product.seller_id,
            title="商品已被下架",
            content=f"您发布的商品「{product.title}」因违规已被管理员下架，如有疑问请联系平台。",
        )
        return ok({"id": product.id}, "商品已下架")


# ---------------- 数据统计 ----------------
class AdminStatsView(APIView):
    """GET /api/v1/admin/stats/ 平台数据统计（后台首页 + ECharts 用）。"""

    permission_classes = [IsAdminUser]

    def get(self, request) -> Response:
        from apps.orders.models import Order, OrderStatus
        from apps.users.models import User

        today = timezone.localtime().date()

        total_users = User.objects.count()
        total_products = Product.objects.count()
        total_orders = Order.objects.count()
        # 成交额口径：已支付（含已发货、已完成）的订单金额合计
        paid_statuses = (OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.COMPLETED)
        total_amount = (
            Order.objects.filter(status__in=paid_statuses).aggregate(s=Sum("amount"))["s"]
            or Decimal("0.00")
        )
        pending_products = Product.objects.filter(status=Product.PENDING).count()

        # 分类商品数分布（饼图）
        category_dist = list(
            Category.objects.annotate(cnt=Count("products"))
            .order_by("-cnt")
            .values("name", "cnt")
        )

        data = {
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_amount": str(total_amount),
            "pending_products": pending_products,
            "today_new_users": User.objects.filter(date_joined__date=today).count(),
            "today_new_products": Product.objects.filter(created_at__date=today).count(),
            "today_new_orders": Order.objects.filter(created_at__date=today).count(),
            "category_dist": category_dist,
        }
        return ok(data)