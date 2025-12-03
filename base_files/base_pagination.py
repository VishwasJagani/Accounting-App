# Rest Framework
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for paginating a list of courses.

    This pagination class extends DRF's PageNumberPagination and adds additional metadata
    to the paginated response, such as links to the next and previous pages, the total number
    of items, the current page number, and the page size.
    """

    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 50  # Maximum number of items per page

    def get_paginated_response(self, data):
        """
        Customizes the paginated response with additional metadata.
        """
        # if not len(data):
        #     return Response(
        #         {"success": False, "message": "Data not found."}, status=status.HTTP_400_BAD_REQUEST)

        current_page = self.page.number if self.page is not None else 0
        total_items = self.page.paginator.count if self.page is not None else 0

        # Set page_size to the length of data if it's less than 10
        page_size = len(data) if len(
            data) < self.page_size else self.get_page_size(self.request)

        total_pages = self.page.paginator.num_pages if self.page is not None else 0

        api_type = self.request.query_params.get('api_type', 'json')

        if api_type == "app":
            return Response({
                "success": True,
                "message": "Data fetched successfully.",
                "data": {
                    'links': {
                        'next': self.get_next_link(),
                        'previous': self.get_previous_link()
                    },
                    'total': total_items,
                    'page': current_page,
                    'page_size': page_size,
                    'total_pages': max(1, total_pages),
                    'results': data
                }
            })

        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'total': total_items,
            'page': current_page,
            'page_size': page_size,
            'total_pages': max(1, total_pages),
            "success": True,
            'results': data,
        }) if self.page is not None else Response({
            'links': {},
            'total': 0,
            'page': 0,
            'page_size': page_size,
            'total_pages': 0,
            "success": True,
            'results': [],
        })
