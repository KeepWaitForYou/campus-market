"""订单后台管理：Django admin 注册。"""
from django.contrib import admin

from apps.orders.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "buyer", "seller", "product", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order_no", "buyer__username", "seller__username", "product__title")
    readonly_fields = ("order_no", "created_at", "updated_at")