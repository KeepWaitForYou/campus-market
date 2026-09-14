"""订单模块路由：/api/v1/orders/"""
from django.urls import path

from apps.orders.views import (
    OrderCancelView,
    OrderConfirmView,
    OrderDetailView,
    OrderListCreateView,
    OrderPayView,
    OrderShipView,
)

urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="order_list_create"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path("orders/<int:order_id>/pay/", OrderPayView.as_view(), name="order_pay"),
    path("orders/<int:order_id>/cancel/", OrderCancelView.as_view(), name="order_cancel"),
    path("orders/<int:order_id>/ship/", OrderShipView.as_view(), name="order_ship"),
    path("orders/<int:order_id>/confirm/", OrderConfirmView.as_view(), name="order_confirm"),
]