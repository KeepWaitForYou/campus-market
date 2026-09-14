"""用户资料相关路由：/api/v1/users/"""
from django.urls import path

from apps.users.views import AvatarUploadView, UserMeView

urlpatterns = [
    path("users/me/", UserMeView.as_view(), name="user_me"),
    path("users/me/avatar/", AvatarUploadView.as_view(), name="user_avatar"),
]