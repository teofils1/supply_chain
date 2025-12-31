"""
Custom pagination classes for the Supply Chain API.

Provides configurable pagination with additional metadata and
performance optimizations.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """
    Standard pagination for list endpoints.

    Features:
    - Configurable page size via query parameter
    - Maximum page size limit to prevent abuse
    - Rich metadata in response (total count, pages, links)
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        """Return pagination metadata with results."""
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        """Schema for API documentation."""
        return {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Total number of items",
                    "example": 100,
                },
                "total_pages": {
                    "type": "integer",
                    "description": "Total number of pages",
                    "example": 4,
                },
                "current_page": {
                    "type": "integer",
                    "description": "Current page number",
                    "example": 1,
                },
                "page_size": {
                    "type": "integer",
                    "description": "Number of items per page",
                    "example": 25,
                },
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "description": "URL to next page",
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "description": "URL to previous page",
                },
                "results": schema,
            },
        }


class LargeResultsPagination(PageNumberPagination):
    """
    Pagination for endpoints that may return large datasets.

    Uses larger default page size but still enforces limits.
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
    page_query_param = "page"

    def get_paginated_response(self, data):
        """Return pagination metadata with results."""
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class SmallResultsPagination(PageNumberPagination):
    """
    Pagination for endpoints with detailed results.

    Smaller page size for complex nested data.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
    page_query_param = "page"

    def get_paginated_response(self, data):
        """Return pagination metadata with results."""
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
