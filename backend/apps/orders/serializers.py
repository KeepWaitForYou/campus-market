"""订单模块序列化器。"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.orders.models import Order
from apps.products.models import Product

User = get_user_model()


# ---------------- 内嵌摘要 ----------------
class UserBriefSerializer(serializers.ModelSerializer):
    """买家/卖家简要信息。"""

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "nickname", "avatar_url")

    def get_avatar_url(self, obj: "User") -> str | None:
        if obj.avatar:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None


class ProductBriefSerializer(serializers.ModelSerializer):
    """订单内商品简要信息。"""

    cover = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Product
        fields = ("id", "title", "price", "cover", "status", "status_label", "campus", "location")

    def get_cover(self, obj: Product) -> str | None:
        cover = obj.images.filter(is_cover=True).first() or obj.images.first()
        if cover:
            request = self.context.get("request")
            return request.build_absolute_uri(cover.image.url) if request else cover.image.url
        return None


# ---------------- 订单 ----------------
class OrderListSerializer(serializers.ModelSerializer):
    """订单列表项。"""

    status_label = serializers.CharField(source="get_status_display", read_only=True)
    product = ProductBriefSerializer(read_only=True)
    buyer = UserBriefSerializer(read_only=True)
    seller = UserBriefSerializer(read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "order_no",
            "product",
            "buyer",
            "seller",
            "amount",
            "status",
            "status_label",
            "role",
            "remark",
            "pay_time",
            "ship_time",
            "finish_time",
            "cancel_time",
            "created_at",
        )

    def get_role(self, obj: Order) -> str:
        """当前请求用户在此订单中的角色：bought / sold / admin。"""
        user = self.context["request"].user
        if obj.buyer_id == user.id:
            return "bought"
        if obj.seller_id == user.id:
            return "sold"
        return "admin"


class OrderDetailSerializer(OrderListSerializer):
    """订单详情：额外包含商品描述。"""

    product = ProductBriefSerializer(read_only=True)

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + ("product_description",)

    product_description = serializers.CharField(source="product.description", read_only=True)


class OrderCreateSerializer(serializers.Serializer):
    """创建订单：仅需商品 id 与可选备注。"""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    remark = serializers.CharField(required=False, allow_blank=True, max_length=200)