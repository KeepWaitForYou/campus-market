"""商品/分类/收藏路由：/api/v1/"""
from django.urls import path

from apps.products.views import (
    CategoryListView,
    FavoriteListView,
    FavoriteView,
    HotSearchesView,
    ProductDetailView,
    ProductListCreateView,
    ProductOffShelfView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("products/", ProductListCreateView.as_view(), name="product_list_create"),
    path("products/hot_searches/", HotSearchesView.as_view(), name="hot_searches"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("products/<int:pk>/off_shelf/", ProductOffShelfView.as_view(), name="product_off_shelf"),
    path(
        "products/<int:product_id>/favorite/",
        FavoriteView.as_view(),
        name="product_favorite",
    ),
    path("favorites/", FavoriteListView.as_view(), name="favorite_list"),
]