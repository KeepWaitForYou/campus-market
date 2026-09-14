"""
统一响应格式。

约定：所有 API 返回体结构为

    {
      "code": 0,           # 0 表示成功；非 0 表示业务失败（与 HTTP 状态码一致）
      "message": "ok",     # 提示信息
      "data": { ... }      # 业务数据
    }

分页数据固定为 { count, next, previous, results }。
"""
from typing import Any

from rest_framework.response import Response


def ok(data: Any = None, message: str = "ok", status: int = 200) -> Response:
    """成功响应。"""
    return Response({"code": 0, "message": message, "data": data}, status=status)


def fail(
    message: str = "请求失败", data: Any = None, status: int = 400, code: int | None = None
) -> Response:
    """失败响应：code 默认等于 HTTP 状态码。"""
    return Response(
        {"code": code if code is not None else status, "message": message, "data": data},
        status=status,
    )