"""后台管理路由（商品部分）：/api/v1/admin/"""
from django.urls import path

from apps.products.views_admin import (
    AdminStatsView,
    ApproveProductView,
    CategoryAdminDetailView,
    CategoryAdminListView,
    ForbidProductView,
    PendingProductListView,
    RejectProductView,
)

urlpatterns = [
    # 商品审核
    path("products/pending/", PendingProductListView.as_view(), name="admin_product_pending"),
    path("products/<int:product_id>/approve/", ApproveProductView.as_view(), name="admin_product_approve"),
    path("products/<int:product_id>/reject/", RejectProductView.as_view(), name="admin_product_reject"),
    path("products/<int:product_id>/forbid/", ForbidProductView.as_view(), name="admin_product_forbid"),
    # 分类管理（GET 全量列表 / POST 新增）
    path("categories/", CategoryAdminListView.as_view(), name="admin_category_list"),
    path("categories/<int:category_id>/", CategoryAdminDetailView.as_view(), name="admin_category_detail"),
    # 数据统计
    path("stats/", AdminStatsView.as_view(), name="admin_stats"),
]