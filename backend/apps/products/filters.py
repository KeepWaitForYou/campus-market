"""商品过滤：django-filter 定义可筛选参数。"""
import django_filters
from django_filters.rest_framework import FilterSet

from apps.products.models import Product


class ProductFilter(FilterSet):
    """商品筛选：分类、价格区间、成色、校区、状态（默认在售）。"""

    category = django_filters.NumberFilter(field_name="category_id")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    condition = django_filters.CharFilter(field_name="condition")
    campus = django_filters.CharFilter(field_name="campus", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status")

    class Meta:
        model = Product
        fields = ["category", "min_price", "max_price", "condition", "campus", "status"]