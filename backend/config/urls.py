"""URL 路由总入口。"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django Admin（备用管理入口）
    path("admin/", admin.site.urls),
    # 业务 API（统一前缀 /api/v1/）
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/", include("apps.products.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.users.urls_user")),
    path("api/v1/admin/", include("apps.products.urls_admin")),
    path("api/v1/admin/", include("apps.orders.urls_admin")),
    path("api/v1/admin/", include("apps.users.urls_admin")),
    # API 文档
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/v1/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)