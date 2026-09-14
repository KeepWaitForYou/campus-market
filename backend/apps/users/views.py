"""用户视图：注册、登录、刷新、个人资料、头像上传。"""
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.permissions import IsSelfOrAdmin
from apps.common.response import fail, ok
from apps.users.models import User
from apps.users.serializers import (
    CustomTokenObtainPairSerializer,
    LoginResponseSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    AvatarUploadSerializer,
)


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ 新用户注册，成功后直接返回 token。"""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: User = serializer.save()
        data = LoginResponseSerializer.build(user)
        return ok(data, message="注册成功", status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/ 用户名+密码登录，返回 access/refresh 与用户信息。"""

    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: User = serializer.user
        # 记录最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        data = {
            "access": serializer.validated_data["access"],
            "refresh": serializer.validated_data["refresh"],
            "user": UserSerializer(user, context={"request": request}).data,
        }
        return ok(data, message="登录成功")


class UserMeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/users/me/ 查看与修改个人资料。"""

    permission_classes = [IsAuthenticated, IsSelfOrAdmin]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self) -> User:
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs) -> Response:
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(request.user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(
            UserSerializer(request.user, context={"request": request}).data,
            message="资料已更新",
        )


class AvatarUploadView(APIView):
    """POST /api/v1/users/me/avatar/ 上传/更换头像（multipart）。"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request) -> Response:
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: User = request.user
        user.avatar = serializer.validated_data["avatar"]
        user.save(update_fields=["avatar"])
        return ok(
            UserSerializer(user, context={"request": request}).data["avatar_url"],
            message="头像上传成功",
        )