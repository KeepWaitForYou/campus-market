"""用户后台管理路由：/api/v1/admin/"""
from django.urls import path

from apps.users.views_admin import UserAdminListView, UserToggleActiveView

urlpatterns = [
    path("users/", UserAdminListView.as_view(), name="admin_user_list"),
    path(
        "users/<int:user_id>/toggle_active/",
        UserToggleActiveView.as_view(),
        name="admin_user_toggle_active",
    ),
]