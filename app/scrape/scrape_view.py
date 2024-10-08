from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync
import logging

from ..services.web_request_service import WebRequestService
from ..services.dom_extractor_service import DomExtractorService

logger = logging.getLogger(__name__)

class WebScrapeView(APIView):
    """
    API view for scraping web content and extracting specific DOM elements based on user input.

    This view handles both static and dynamic web pages, with optional proxy support and pagination.
    It provides query parameters for filtering DOM elements and customizing the scraping process.
    """

    def __init__(self, **kwargs):
        """
        Initialize the WebScrapeView with services for web scraping and DOM extraction.

        :param kwargs: Additional keyword arguments passed to the APIView initializer.
        """
        super().__init__(**kwargs)
        self.web_service = WebRequestService()  # Service for handling web requests
        self.dom_extractor_service = DomExtractorService()  # Service for DOM extraction

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to scrape web content based on query parameters.

        This method validates required parameters (URL and class_name), performs web scraping (using Playwright),
        and extracts data from the HTML based on the specified DOM structure. It supports pagination and proxy usage.

        :param request: The GET request object containing query parameters.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: A Response object with the scraped data and the total number of pages, or an error response.
        """
        # Extract query parameters
        url, class_name, user_proxy, has_pagination, pagination_class, white_list, menu_selector = self.get_query_params(request)

        # Validating required parameters
        if not url:
            return self.error_response("URL parameter is required", status.HTTP_400_BAD_REQUEST)
        if not class_name:
            return self.error_response("Class name parameter is required", status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch HTML content using the async web scraping service
            html_content = async_to_sync(self.web_service.fetch_with_playwright)(url, menu_selector)

            if not html_content:
                return self.error_response(f"Unable to fetch content from {url}", status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Parse the content and handle potential parsing errors
            soup = self.dom_extractor_service.parse(html_content)
            if not soup:
                return self.error_response("Error parsing the content", status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Handle pagination logic if applicable
            total_pages = self.dom_extractor_service.get_total_pages(soup, has_pagination, pagination_class)

            # Use the appropriate method to get data based on the presence of a whitelist
            if white_list and len(white_list) > 0:
                data = self.dom_extractor_service.get_selected_elements_in_class(soup, class_name, white_list)
            else:
                data = self.dom_extractor_service.get_all_elements_in_class(soup, class_name)

            return Response({"scraped_data": data, "total_pages": total_pages}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in scraping: {str(e)}", exc_info=True)
            return self.error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_query_params(self, request):
        """
        Extract and sanitize query parameters from the request.

        This method retrieves necessary parameters like URL, class name, and optional ones such as proxy usage, 
        pagination information, and whitelist of DOM elements.

        :param request: The GET request object.
        :return: A tuple of sanitized query parameters (url, class_name, user_proxy, has_pagination, pagination_class, white_list, menu_selector).
        """
        url = request.query_params.get('url')
        class_name = request.query_params.get('class_name')
        user_proxy = request.query_params.get('user_proxy', 'false').lower()
        has_pagination = request.query_params.get('has_paginate', 'false').lower()
        white_list = request.query_params.getlist('white_list', [])  # Use getlist to handle multiple values
        pagination_class = None if has_pagination == 'false' else request.query_params.get('pagination_class')
        menu_selector = request.query_params.get('menu_selector_class')
        return url, class_name, user_proxy, has_pagination, pagination_class, white_list, menu_selector

    def error_response(self, message, status_code):
        """
        Helper method to return standardized error responses.

        :param message: The error message to include in the response.
        :param status_code: The HTTP status code for the error response.
        :return: A Response object containing the error message and status code.
        """
        return Response({"error": message}, status=status_code)
