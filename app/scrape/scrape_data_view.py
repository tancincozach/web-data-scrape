import logging
from urllib.parse import urlsplit

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..client_management.authentication import ClientAuthentication
from ..client_management.permissions import IsClient
from ..client_management.throttling import ClientRateThrottle
from ..services.exceptions import (
    FetchError,
    FetchTimeoutError,
    ParseError,
    UnsafeUrlError,
)
from .serializers import ScrapeRequestSerializer
from .services import ScrapeService

logger = logging.getLogger(__name__)


class WebScrapeView(APIView):
    """API view for fetching a page and extracting elements by class name."""

    authentication_classes = [ClientAuthentication]
    permission_classes = [IsClient]
    throttle_classes = [ClientRateThrottle]

    def __init__(self, scrape_service=None, **kwargs):
        super().__init__(**kwargs)
        self.scrape_service = scrape_service or ScrapeService.from_settings()

    def get(self, request, *args, **kwargs):
        """Scrape ``url`` and return elements matching ``class_name``."""
        serializer = ScrapeRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return self.error_response(
                "Invalid request parameters.",
                status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        url = serializer.validated_data["url"]
        class_names = serializer.validated_data["class_name"]

        try:
            data = self.scrape_service.scrape(url, class_names)
            return Response({"scraped_data": data}, status=status.HTTP_200_OK)

        except UnsafeUrlError:
            logger.warning("Rejected unsafe scraping target host=%s", self._host(url))
            return self.error_response(
                "The URL is not allowed.", status.HTTP_400_BAD_REQUEST
            )
        except FetchTimeoutError:
            logger.warning("Scraping timed out host=%s", self._host(url))
            return self.error_response(
                "The target took too long to respond.",
                status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except FetchError:
            logger.warning("Scraping fetch failed host=%s", self._host(url))
            return self.error_response(
                "Unable to fetch the target URL.",
                status.HTTP_502_BAD_GATEWAY,
            )
        except ParseError:
            logger.warning("Scraping parse failed host=%s", self._host(url))
            return self.error_response(
                "Unable to parse the target page.",
                status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            logger.exception("Unexpected error while scraping host=%s", self._host(url))
            return self.error_response(
                "An unexpected error occurred.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def _host(url):
        try:
            return urlsplit(url).hostname or "unknown"
        except ValueError:
            return "unknown"

    def error_response(self, message, status_code, details=None):
        """Return a standardized error response."""
        payload = {"error": message}
        if details:
            payload["details"] = details
        return Response(payload, status=status_code)
