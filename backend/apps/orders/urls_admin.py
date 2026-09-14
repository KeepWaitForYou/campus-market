"""订单后台管理路由：/api/v1/admin/orders/"""
from django.urls import path

from apps.orders.views_admin import AdminOrderListView

urlpatterns = [
    path("orders/", AdminOrderListView.as_view(), name="admin_order_list"),
]