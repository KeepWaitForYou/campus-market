"""
统一异常处理。

将 Django/DRF 的异常转换为统一响应体 {code, message, data}，
并记录 500 级别错误的日志。AutoSchema 文档绘制不受影响。
"""
import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("campus_market")


def custom_exception_handler(exc: Exception, context: dict) -> Response:
    """DRF 全局异常处理器入口。"""
    # 先调 DRF 默认处理器拿到标准响应
    response = exception_handler(exc, context)

    if response is None:
        # 未被 DRF 识别：转为统一 500
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return Response(
            {"code": 500, "message": "服务器内部错误", "data": None},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 提取最小可读的错误信息
    message = _flatten_error(response.data)
    return Response(
        {
            "code": response.status_code,
            "message": message,
            "data": None,
        },
        status=response.status_code,
    )


def _flatten_error(data) -> str:
    """把 DRF 校验错误扁平化为单条可读信息。"""
    if data is None:
        return "请求失败"
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        return _flatten_error(data[0]) if data else "请求失败"
    if isinstance(data, dict):
        # 非字段错误（如认证失败、权限不足）
        if "detail" in data:
            return _flatten_error(data["detail"])
        # 字段级错误：取第一个字段的第一条
        first_key = next(iter(data))
        return f"{first_key}: {_flatten_error(data[first_key])}"
    return str(data)