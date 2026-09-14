"""用户序列化器：注册 / 登录 / 资料 / 头像。"""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """注册：用户名、密码、邮箱、手机号、昵称、学号。"""

    password = serializers.CharField(
        write_only=True, min_length=6, max_length=128, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True, min_length=6, max_length=128, style={"input_type": "password"}
    )
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "confirm_password",
            "email",
            "phone",
            "nickname",
            "student_no",
        )
        extra_kwargs = {
            "phone": {"required": False, "allow_blank": True},
            "nickname": {"required": False, "allow_blank": True},
            "student_no": {"required": False, "allow_blank": True},
        }

    def validate_username(self, value: str) -> str:
        """用户名需唯一。"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已被注册")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError("两次输入的密码不一致")
        return attrs

    def create(self, validated_data: dict) -> User:
        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            phone=validated_data.get("phone", ""),
            nickname=validated_data.get("nickname", ""),
            student_no=validated_data.get("student_no", ""),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """用户资料展示。"""

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "nickname",
            "phone",
            "email",
            "avatar",
            "avatar_url",
            "student_no",
            "is_verified",
            "is_staff",
            "is_superuser",
            "date_joined",
        )
        read_only_fields = ("id", "username", "date_joined", "is_verified", "is_staff", "is_superuser")

    def get_avatar_url(self, obj: User) -> str | None:
        """返回头像的绝对地址（代理后以 /media/ 开头）。"""
        if obj.avatar:
            request = self.context.get("request")
            url = obj.avatar.url
            return request.build_absolute_uri(url) if request else url
        return None


class UserUpdateSerializer(serializers.ModelSerializer):
    """修改昵称、手机号、邮箱。"""

    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("nickname", "phone", "email")
        extra_kwargs = {
            "nickname": {"required": False, "allow_blank": True},
            "phone": {"required": False, "allow_blank": True},
        }


class AvatarUploadSerializer(serializers.Serializer):
    """头像上传（multipart/form-data）。"""

    avatar = serializers.ImageField()

    def validate_avatar(self, value):
        # 简单类型限制，避免超大或非图片文件
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("图片大小不能超过 5MB")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """登录：在 token 中加入用户名，便于前端展示。"""

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        token["username"] = user.username
        token["nickname"] = user.nickname
        return token


class LoginResponseSerializer(serializers.Serializer):
    """登录/注册成功后的响应：access + refresh + user。"""

    @staticmethod
    def build(user: User) -> dict:
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }


class AdminUserSerializer(serializers.ModelSerializer):
    """管理员视角的用户信息（含账号状态）。"""

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "nickname",
            "phone",
            "email",
            "student_no",
            "avatar_url",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_verified",
            "date_joined",
            "last_login",
        )
        read_only_fields = fields

    def get_avatar_url(self, obj: User) -> str | None:
        if obj.avatar:
            request = self.context.get("request")
            url = obj.avatar.url
            return request.build_absolute_uri(url) if request else url
        return None