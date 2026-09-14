"""Django Admin 注册商品相关模型。"""
from django.contrib import admin

from apps.products.models import Category, Favorite, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """分类管理：新增、编辑、禁用。"""

    list_display = ("id", "name", "sort", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("sort", "id")
    list_editable = ("sort", "is_active")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """商品管理：审核、下架违规商品。"""

    list_display = (
        "id",
        "title",
        "seller",
        "category",
        "price",
        "condition",
        "campus",
        "status",
        "view_count",
        "favorite_count",
        "created_at",
    )
    list_filter = ("status", "condition", "category", "campus")
    search_fields = ("title", "description", "seller__username")
    inlines = [ProductImageInline]
    actions = ["approve_products", "force_off_shelf"]

    @admin.action(description="审核通过所选商品")
    def approve_products(self, request, queryset):
        updated = queryset.filter(status=Product.PENDING).update(status=Product.ON_SALE)
        self.message_user(request, f"已通过 {updated} 件商品")

    @admin.action(description="强制下架所选商品")
    def force_off_shelf(self, request, queryset):
        updated = queryset.exclude(status=Product.OFF_SHELF).update(status=Product.OFF_SHELF)
        self.message_user(request, f"已下架 {updated} 件商品")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "created_at")
    search_fields = ("user__username", "product__title")