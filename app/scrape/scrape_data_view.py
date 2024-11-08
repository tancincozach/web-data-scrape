from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync

from ..services.web_request_service import WebRequestService
from ..services.dom_extractor_service import DomExtractorService
from ..services.logger_service import LoggerService

class WebScrapeView(APIView):
    """
    API view for scraping web content and extracting specific DOM elements based on user input.

    This view handles both static and dynamic web pages, with optional proxy support and pagination.
    """

    def __init__(self, **kwargs):
        """
        Initialize the WebScrapeView with services for web scraping and DOM extraction.
        """
        super().__init__(**kwargs)
        self.web_service = WebRequestService()  # Service for handling web requests
        self.dom_extractor_service = DomExtractorService()  # Service for DOM extraction
        self.logger_service = LoggerService(__name__)

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to scrape web content based on query parameters.
        
        The request should contain `class_name` (a list of class names) and `element_type` (HTML tag type).
        
        :param request: The GET request object containing JSON data with scrape metadata.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: A Response object with the scraped data or an error response.
        """
        # Extract class names and element type from query parameters
        class_name = request.query_params.getlist('class_name')
        url = request.query_params.get('url')

        if not class_name:
            return self.error_response("class_name is required and should be a list", status.HTTP_400_BAD_REQUEST)
        
        if not url:
            return self.error_response("URL is required", status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch HTML content asynchronously
            html_content = async_to_sync(self.web_service.fetch_with_playwright)(url)

            if not html_content:
                return self.error_response(f"Unable to fetch content from {url}", status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Parse the content
            soup = self.dom_extractor_service.parse(html_content)
            if not soup:
                return self.error_response("Error parsing the content", status.HTTP_500_INTERNAL_SERVER_ERROR)

            data = self.dom_extractor_service.get_elements(soup, class_name)
            return Response({"scraped_data": data }, status=status.HTTP_200_OK)

        except Exception as e:
            self.logger_service.error(f"Error in scraping: {str(e)}", True)
            return self.error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def error_response(self, message, status_code):
        """
        Helper method to return standardized error responses.
        """
        return Response({"error": message}, status=status_code)
