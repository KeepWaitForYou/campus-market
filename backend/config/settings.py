"""
校园二手交易平台 - Django 主配置
所有敏感配置通过环境变量注入（.env 使用 python-dotenv 加载）。
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# ---------- 基础路径 ----------
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env（容器内由 env_file 注入的环境变量优先级更高，不会覆盖）
load_dotenv(BASE_DIR / ".env")


def env_bool(key: str, default: str = "0") -> bool:
    """读取布尔型环境变量。"""
    return os.getenv(key, default).strip().lower() in ("1", "true", "yes", "on")


def env_list(key: str, default: str = "") -> list[str]:
    """读取逗号分隔的环境变量。"""
    raw = os.getenv(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ---------- Django 核心 ----------
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-key")
DEBUG = env_bool("DEBUG", "0")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,nginx,backend")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # 业务应用
    "apps.common",
    "apps.users",
    "apps.products",
    "apps.orders",
    "apps.notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------- 数据库：MySQL 8.0 ----------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE", "campus_market"),
        "USER": os.getenv("MYSQL_USER", "campus"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", "campus123456"),
        "HOST": os.getenv("MYSQL_HOST", "mysql"),
        "PORT": os.getenv("MYSQL_PORT", "3306"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# ---------- 缓存：Redis ----------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/0"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "campus_market",
        "TIMEOUT": 300,
    }
}

# ---------- 用户模型 ----------
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

# ---------- DRF ----------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.common.authentication.ActiveUserJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
    "NON_FIELD_ERRORS_KEY": "detail",
}

# ---------- SimpleJWT ----------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------- CORS ----------
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)

# ---------- 静态与媒体 ----------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 上传大小与类型限制
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

# ---------- Celery ----------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_ENABLE_UTC = False
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# 业务参数：订单超时未支付自动取消（秒）
ORDER_TIMEOUT_SECONDS = int(os.getenv("ORDER_TIMEOUT_SECONDS", "1800"))

# ---------- drf-spectacular 文档 ----------
SPECTACULAR_SETTINGS = {
    "TITLE": "校园二手交易平台 API",
    "DESCRIPTION": "校园二手交易平台 RESTful API 文档（JWT 鉴权，登录后点击 Authorize 填入 access token）",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "认证", "description": "注册 / 登录 / 刷新 token"},
        {"name": "用户", "description": "个人资料 / 头像"},
        {"name": "分类", "description": "商品分类"},
        {"name": "商品", "description": "商品发布、搜索、详情、收藏"},
        {"name": "收藏", "description": "我的收藏"},
        {"name": "订单", "description": "下单、支付、发货、确认收货、取消"},
        {"name": "通知", "description": "站内通知"},
        {"name": "管理后台", "description": "商品审核 / 用户管理 / 订单管理 / 统计（需管理员）"},
    ],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- 国际化和时区 ----------
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True