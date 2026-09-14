"""用户后台管理视图：用户列表、禁用/启用。"""
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.response import fail, ok
from apps.users.models import User
from apps.users.serializers import AdminUserSerializer


class UserAdminListView(generics.ListAPIView):
    """GET /api/v1/admin/users/ 用户列表（分页）。

    支持筛选：
    - ?search=关键词      用户名 / 昵称 / 学号 / 手机号
    - ?is_active=0|1      按账号状态
    - ?is_staff=0|1       仅看普通用户 / 管理员
    """

    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        qs = User.objects.all()
        keyword = (self.request.query_params.get("search") or "").strip()
        if keyword:
            qs = qs.filter(
                Q(username__icontains=keyword)
                | Q(nickname__icontains=keyword)
                | Q(student_no__icontains=keyword)
                | Q(phone__icontains=keyword)
            )
        is_active = (self.request.query_params.get("is_active") or "").strip()
        if is_active in ("0", "1"):
            qs = qs.filter(is_active=(is_active == "1"))
        is_staff = (self.request.query_params.get("is_staff") or "").strip()
        if is_staff in ("0", "1"):
            qs = qs.filter(is_staff=(is_staff == "1"))
        return qs.order_by("-date_joined")


class UserToggleActiveView(APIView):
    """POST /api/v1/admin/users/{id}/toggle_active/ 禁用 / 启用用户。

    禁用后：该用户已签发的 JWT 立即失效（见 ActiveUserJWTAuthentication），且无法再登录。
    """

    permission_classes = [IsAdminUser]

    def post(self, request, user_id: int):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return fail("用户不存在", status=status.HTTP_404_NOT_FOUND)
        if user.id == request.user.id:
            return fail("不能禁用自己")
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        action = "已启用" if user.is_active else "已禁用"
        return ok({"id": user.id, "is_active": user.is_active}, f"用户{action}")