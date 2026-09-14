"""
通用权限。

- IsAdminUser：管理员（is_staff 或 is_superuser）
- IsOwnerOrReadOnly：读操作所有人可访问；写操作仅资源所有者
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """仅管理员（staff / superuser）可访问。"""

    message = "需要管理员权限"

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """对象拥有的用户可写，其他用户只读。"""

    message = "无权操作该资源"

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        # 商品/订单等对象需支持 owner 属性（seller/buyer）
        owner = getattr(obj, "owner", None)
        if owner is None:
            owner = getattr(obj, "seller", None) or getattr(obj, "buyer", None)
        return owner == request.user


class IsSelfOrAdmin(permissions.BasePermission):
    """仅本人或管理员可访问。"""

    message = "无权查看他人信息"

    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            obj == request.user
            or (request.user.is_authenticated and request.user.is_staff)
        )