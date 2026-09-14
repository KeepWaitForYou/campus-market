"""商品模块序列化器。"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.response import fail
from apps.products.models import Category, Favorite, Product, ProductImage
from apps.products.tasks import compress_image_task

User = get_user_model()


# ---------------- 分类 ----------------
class CategorySerializer(serializers.ModelSerializer):
    """分类展示。"""

    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "sort", "is_active", "product_count")

    def to_representation(self, instance: Category) -> dict:
        """附加在售商品数（列表页展示用）。"""
        data = super().to_representation(instance)
        data["product_count"] = instance.products.filter(status=Product.ON_SALE).count()
        return data


# ---------------- 图片 ----------------
class ProductImageSerializer(serializers.ModelSerializer):
    """图片展示：返回绝对/相对 URL。"""

    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ("id", "url", "is_cover", "sort")

    def get_url(self, obj: ProductImage) -> str:
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


# ---------------- 卖家信息 ----------------
class SellerSerializer(serializers.ModelSerializer):
    """卖家简要信息。"""

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "nickname", "avatar_url")

    def get_avatar_url(self, obj: "User") -> str | None:
        if obj.avatar:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None


# ---------------- 商品 ----------------
class ProductListSerializer(serializers.ModelSerializer):
    """商品列表项：封面图、价格、成色、校区、卖家昵称。"""

    cover = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)
    condition_label = serializers.CharField(source="get_condition_display", read_only=True)
    seller_nickname = serializers.CharField(source="seller.display_name", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "title",
            "price",
            "original_price",
            "condition",
            "condition_label",
            "campus",
            "location",
            "cover",
            "category_name",
            "seller_nickname",
            "view_count",
            "favorite_count",
            "status",
            "created_at",
        )

    def get_cover(self, obj: Product) -> str | None:
        cover = obj.images.filter(is_cover=True).first() or obj.images.first()
        if cover:
            request = self.context.get("request")
            return request.build_absolute_uri(cover.image.url) if request else cover.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """商品详情：图片列表 + 卖家信息 + 收藏状态。"""

    images = ProductImageSerializer(many=True, read_only=True)
    seller = SellerSerializer(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    condition_label = serializers.CharField(source="get_condition_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "title",
            "description",
            "price",
            "original_price",
            "condition",
            "condition_label",
            "campus",
            "location",
            "status",
            "status_label",
            "reject_reason",
            "view_count",
            "favorite_count",
            "category",
            "category_name",
            "images",
            "seller",
            "is_favorite",
            "created_at",
            "updated_at",
        )

    def get_is_favorite(self, obj: Product) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False


class ProductCreateSerializer(serializers.ModelSerializer):
    """发布商品：支持 multipart 多图上传（images 字段为文件列表）。"""

    images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False, max_length=9, allow_empty=True
    )

    class Meta:
        model = Product
        fields = (
            "title",
            "description",
            "price",
            "original_price",
            "condition",
            "campus",
            "location",
            "category",
            "images",
        )
        extra_kwargs = {
            "original_price": {"required": False, "allow_null": True},
            "campus": {"required": False, "allow_blank": True},
            "location": {"required": False, "allow_blank": True},
        }

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("售价必须大于 0")
        return value

    def create(self, validated_data: dict) -> Product:
        images = validated_data.pop("images", [])
        product = Product.objects.create(seller=self.context["request"].user, **validated_data)
        # 保存图片；压缩由 Celery 异步处理
        for index, img in enumerate(images):
            instance = ProductImage.objects.create(
                product=product, image=img, is_cover=(index == 0), sort=index
            )
            compress_image_task.delay(instance.id)
        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    """编辑商品基本信息；不传 images 则保留原图。"""

    images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False, max_length=9, allow_empty=True
    )

    class Meta:
        model = Product
        fields = (
            "title",
            "description",
            "price",
            "original_price",
            "condition",
            "campus",
            "location",
            "category",
            "images",
        )
        extra_kwargs = {
            "title": {"required": False},
            "price": {"required": False},
            "category": {"required": False},
        }

    def update(self, instance: Product, validated_data: dict) -> Product:
        images = validated_data.pop("images", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        # 若上传了新图，则替换旧图（保持第一张为封面）
        if images:
            instance.images.all().delete()
            for index, img in enumerate(images):
                new_image = ProductImage.objects.create(
                    product=instance, image=img, is_cover=(index == 0), sort=index
                )
                compress_image_task.delay(new_image.id)
        return instance


# ---------------- 收藏 ----------------
class FavoriteSerializer(serializers.ModelSerializer):
    """收藏列表项：内嵌商品摘要。"""

    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "product", "created_at")