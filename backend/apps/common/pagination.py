"""统一分页：PageNumberPagination，默认每页 10 条，支持 ?page_size=。"""
from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页：数据放在 data.results 中。"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data) -> Response:
        return Response(
            {
                "code": 0,
                "message": "ok",
                "data": OrderedDict(
                    [
                        ("count", self.page.paginator.count),
                        ("next", self.get_next_link()),
                        ("previous", self.get_previous_link()),
                        ("results", data),
                    ]
                ),
            }
        )