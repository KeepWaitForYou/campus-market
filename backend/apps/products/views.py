"""商品模块视图：分类、商品 CRUD、收藏、热门搜索。"""
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOwnerOrReadOnly
from apps.common.response import fail, ok
from apps.products.filters import ProductFilter
from apps.products.models import Category, Favorite, Product
from apps.products.serializers import (
    CategorySerializer,
    FavoriteSerializer,
    ProductCreateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductUpdateSerializer,
)
from apps.products.tasks import increment_view_count, record_search_keyword

# 首页列表缓存 TTL（秒）
HOME_LIST_CACHE_TTL = 60 * 5


# ---------------- 分类 ----------------
class CategoryListView(generics.ListAPIView):
    """GET /api/v1/categories/ 启用分类列表（带在售商品数）。"""

    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.filter(is_active=True).prefetch_related("products")


# ---------------- 商品 ----------------
class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/products/            商品列表：搜索/筛选/排序/分页
    POST /api/v1/products/            发布商品（登录用户），multipart 多图上传
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["title", "description", "campus", "location"]
    ordering_fields = ["created_at", "price", "view_count", "favorite_count"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCreateSerializer
        return ProductListSerializer

    def get_queryset(self):
        qs = Product.objects.select_related("seller", "category").prefetch_related(
            "images", "favorites"
        )
        # POST 时无需过滤状态（构建完即返回）；列表默认只展示在售
        if self.request.method == "GET":
            # 卖家查看自己的全部商品（含待审核 / 已下架 / 已售出 / 审核不通过），
            # 供前端「我的发布」页使用：GET /api/v1/products/?mine=1
            if self.request.query_params.get("mine") == "1" and self.request.user.is_authenticated:
                return qs.filter(seller=self.request.user)
            qs = qs.filter(status=Product.ON_SALE)
        return qs

    def list(self, request, *args, **kwargs) -> Response:
        """列表：无筛选/搜索条件时命中首页缓存；有搜索时记录热门关键词。"""
        search = request.query_params.get("search", "")
        page = request.query_params.get("page", "1")
        page_size = request.query_params.get("page_size", "10")

        # 热门搜索记录（仅有关键词时）
        if search:
            record_search_keyword.delay(search)

        # 首页缓存命中条件：第一页、默认 10 条、无任何筛选参数、无搜索
        is_cacheable = page == "1" and page_size == "10" and not request.query_params
        cache_key = "products:home_list_v1"
        if is_cacheable:
            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached)

        response = super().list(request, *args, **kwargs)

        if is_cacheable:
            cache.set(cache_key, response.data, HOME_LIST_CACHE_TTL)
        return response

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        # 失效首页缓存，保证新商品立即可见
        cache.delete("products:home_list_v1")
        return ok(
            ProductDetailSerializer(product, context={"request": request}).data,
            message="发布成功，等待管理员审核",
            status=status.HTTP_201_CREATED,
        )


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/products/{id}/   商品详情（游客可看，浏览量异步 +1）
    PATCH  /api/v1/products/{id}/   编辑商品（仅卖家）
    DELETE /api/v1/products/{id}/   删除商品（仅卖家）
    """

    http_method_names = ["get", "patch", "delete"]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "DELETE"):
            return ProductUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        # 详情可见性：在售商品对所有人开放；卖家可查看自己的全部状态
        # （待审核 / 已下架 / 已售出 / 驳回，供编辑回填）；管理员可查看全部
        qs = Product.objects.select_related("seller", "category").prefetch_related(
            "images", "favorites"
        )
        if self.request.method == "GET":
            user = self.request.user
            if user.is_authenticated:
                if user.is_staff:
                    return qs
                return qs.filter(Q(status=Product.ON_SALE) | Q(seller=user))
            qs = qs.filter(status=Product.ON_SALE)
        return qs

    def retrieve(self, request, *args, **kwargs) -> Response:
        instance = self.get_object()
        if not request.user.is_authenticated or request.user != instance.seller:
            increment_view_count.delay(instance.id)
        serializer = self.get_serializer(instance)
        return ok(serializer.data)

    def patch(self, request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete("products:home_list_v1")
        return ok(
            ProductDetailSerializer(instance, context={"request": request}).data,
            message="商品已更新",
        )

    def delete(self, request, *args, **kwargs) -> Response:
        instance = self.get_object()
        instance.delete()
        cache.delete("products:home_list_v1")
        return ok(message="商品已删除")


class ProductOffShelfView(APIView):
    """POST /api/v1/products/{id}/off_shelf/ 卖家下架商品（PATCH 亦可修改状态）。"""

    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def post(self, request, product_id: int) -> Response:
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return fail("商品不存在", status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, product)
        if product.status not in (Product.ON_SALE, Product.PENDING):
            return fail("当前状态不可下架")
        product.status = Product.OFF_SHELF
        product.save(update_fields=["status", "updated_at"])
        cache.delete("products:home_list_v1")
        return ok(message="商品已下架")


# ---------------- 收藏 ----------------
class FavoriteView(APIView):
    """
    POST   /api/v1/products/{id}/favorite/ 收藏（幂等）
    DELETE /api/v1/products/{id}/favorite/ 取消收藏
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, product_id: int) -> Response:
        try:
            product = Product.objects.get(id=product_id, status=Product.ON_SALE)
        except Product.DoesNotExist:
            return fail("商品不存在或不可收藏", status=status.HTTP_404_NOT_FOUND)
        _, created = Favorite.objects.get_or_create(user=request.user, product=product)
        if created:
            product.favorite_count = product.favorites.count()
            product.save(update_fields=["favorite_count"])
        message = "收藏成功" if created else "已在收藏夹中"
        return ok({"favorite": True, "favorite_count": product.favorite_count}, message=message)

    def delete(self, request, product_id: int) -> Response:
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return fail("商品不存在", status=status.HTTP_404_NOT_FOUND)
        deleted, _ = Favorite.objects.filter(user=request.user, product=product).delete()
        if deleted:
            product.favorite_count = product.favorites.count()
            product.save(update_fields=["favorite_count"])
        return ok({"favorite": False, "favorite_count": product.favorite_count}, message="已取消收藏")


class FavoriteListView(generics.ListAPIView):
    """GET /api/v1/favorites/ 我的收藏（分页）。"""

    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related("product__seller", "product__category")
            .prefetch_related("product__images")
        )


# ---------------- 热门搜索 ----------------
class HotSearchesView(APIView):
    """GET /api/v1/products/hot_searches/ 热门搜索 Top10（Redis 缓存）。"""

    permission_classes = [AllowAny]

    def get(self, request) -> Response:
        items = cache.zrevrange("products:hot_searches", 0, 9, withscores=True)
        data = [{"keyword": k.decode("utf-8"), "hot": int(v)} for k, v in items]
        return ok(data)