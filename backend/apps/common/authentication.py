"""自定义 JWT 认证：被禁用（is_active=False）的用户即使持有有效 token 也无法访问。"""
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class ActiveUserJWTAuthentication(JWTAuthentication):
    """在 SimpleJWT 基础上增加账号启用状态校验。"""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not user.is_active:
            raise AuthenticationFailed("账号已被禁用，请联系管理员")
        return user