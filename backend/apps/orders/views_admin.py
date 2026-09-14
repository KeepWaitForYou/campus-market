"""订单后台管理视图：全部订单列表（含筛选）。"""
from django.db.models import Q
from rest_framework import generics

from apps.common.permissions import IsAdminUser
from apps.orders.models import Order
from apps.orders.serializers import OrderListSerializer


class AdminOrderListView(generics.ListAPIView):
    """GET /api/v1/admin/orders/ 管理员查看全部订单。

    支持筛选：
    - ?status=pending|paid|shipped|completed|cancelled
    - ?role=bought|sold  按买家/卖家
    - ?search=关键词      订单号 / 买家用户名 / 卖家用户名
    - ?sort=amount|-amount  按金额排序
    """

    permission_classes = [IsAdminUser]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        qs = (
            Order.objects.select_related("product", "buyer", "seller")
            .prefetch_related("product__images")
        )
        s = (self.request.query_params.get("status") or "").strip()
        if s:
            qs = qs.filter(status=s)

        role = (self.request.query_params.get("role") or "").strip()
        if role == "bought":
            qs = qs.exclude(buyer__is_staff=True)
        elif role == "sold":
            qs = qs.exclude(seller__is_staff=True)

        keyword = (self.request.query_params.get("search") or "").strip()
        if keyword:
            qs = qs.filter(
                Q(order_no__icontains=keyword)
                | Q(buyer__username__icontains=keyword)
                | Q(seller__username__icontains=keyword)
            )

        sort = (self.request.query_params.get("sort") or "").strip()
        if sort in ("amount", "-amount", "created_at", "-created_at"):
            qs = qs.order_by(sort)
        else:
            qs = qs.order_by("-created_at")
        return qs