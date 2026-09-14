"""商品模块模型：Category / Product / ProductImage / Favorite。"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class ProductStatus(models.TextChoices):
    """商品状态机。

    pending   待审核（发布后默认）
    on_sale   在售（审核通过）
    off_shelf 已下架（卖家下架或违规下架）
    sold      已售出（订单完成/支付后由订单系统置位）
    rejected  审核不通过
    """

    PENDING = "pending", "待审核"
    ON_SALE = "on_sale", "在售"
    OFF_SHELF = "off_shelf", "已下架"
    SOLD = "sold", "已售出"
    REJECTED = "rejected", "审核不通过"


class ProductCondition(models.TextChoices):
    """成色等级。"""

    BRAND_NEW = "brand_new", "全新"
    LIKE_NEW = "like_new", "几乎全新"
    LIGHTLY_USED = "lightly_used", "轻微使用"
    USED = "used", "明显使用"
    DAMAGED = "damaged", "有瑕疵/破损"


class Category(models.Model):
    """商品分类。"""

    name = models.CharField("分类名称", max_length=50, unique=True)
    sort = models.IntegerField("排序", default=0, help_text="数值越小越靠前")
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "商品分类"
        verbose_name_plural = verbose_name
        ordering = ["sort", "id"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """二手商品。"""

    # 状态常量子引用，与 ProductStatus 保持一致，业务代码中可简写为 Product.ON_SALE 等
    PENDING = ProductStatus.PENDING
    ON_SALE = ProductStatus.ON_SALE
    OFF_SHELF = ProductStatus.OFF_SHELF
    SOLD = ProductStatus.SOLD
    REJECTED = ProductStatus.REJECTED

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="卖家",
        on_delete=models.CASCADE,
        related_name="products",
    )
    category = models.ForeignKey(
        Category,
        verbose_name="分类",
        on_delete=models.PROTECT,
        related_name="products",
    )
    title = models.CharField("标题", max_length=100)
    description = models.TextField("描述", blank=True, default="")
    price = models.DecimalField("售价", max_digits=10, decimal_places=2)
    original_price = models.DecimalField("原价", max_digits=10, decimal_places=2, null=True, blank=True)
    condition = models.CharField(
        "成色", max_length=20, choices=ProductCondition.choices, default=ProductCondition.USED
    )
    campus = models.CharField("校区", max_length=50, blank=True, default="")
    location = models.CharField("交易地点", max_length=100, blank=True, default="")
    status = models.CharField(
        "状态", max_length=20, choices=ProductStatus.choices, default=ProductStatus.PENDING, db_index=True
    )
    reject_reason = models.CharField("驳回原因", max_length=255, blank=True, default="")
    view_count = models.PositiveIntegerField("浏览量", default=0)
    favorite_count = models.PositiveIntegerField("收藏量", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "商品"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            # 列表页常用组合：在售 + 时间/价格/浏览量排序
            models.Index(fields=["status", "-created_at"], name="idx_product_status_created"),
            models.Index(fields=["status", "-price"], name="idx_product_status_price"),
            models.Index(fields=["status", "-view_count"], name="idx_product_status_views"),
            models.Index(fields=["status", "category"], name="idx_product_status_cat"),
        ]

    def __str__(self) -> str:
        return f"{self.title}({self.get_status_display()})"

    @property
    def owner(self) -> "settings.AUTH_USER_MODEL":
        """通用 owner 属性，供 IsOwnerOrReadOnly 权限使用。"""
        return self.seller

    @property
    def cover_image_url(self) -> str | None:
        """封面图 URL（无绝对地址，序列化器补充 request 上下文）。"""
        cover = self.images.filter(is_cover=True).first() or self.images.first()
        return cover.image.url if cover else None


class ProductImage(models.Model):
    """商品图片：一张封面 + 多张详情图。"""

    product = models.ForeignKey(
        Product, verbose_name="商品", on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField("图片", upload_to="products/%Y/%m/%d/")
    is_cover = models.BooleanField("是否封面", default=False)
    sort = models.PositiveIntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "商品图片"
        verbose_name_plural = verbose_name
        ordering = ["sort", "id"]

    def __str__(self) -> str:
        return f"{self.product.title} - {self.image.name}"


class Favorite(models.Model):
    """收藏：user 与 product 联合唯一。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="用户", on_delete=models.CASCADE, related_name="favorites"
    )
    product = models.ForeignKey(
        Product, verbose_name="商品", on_delete=models.CASCADE, related_name="favorites"
    )
    created_at = models.DateTimeField("收藏时间", auto_now_add=True)

    class Meta:
        verbose_name = "收藏"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="uniq_user_product_favorite"),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.product.title}"