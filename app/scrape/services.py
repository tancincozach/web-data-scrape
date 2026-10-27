from asgiref.sync import async_to_sync
from django.conf import settings

from ..services.dom_extractor_service import DomExtractorService
from ..services.web_request_service import WebRequestService


class ScrapeService:
    """Orchestrate fetching, parsing, and DOM extraction."""

    def __init__(self, web_service=None, dom_extractor_service=None):
        self.web_service = web_service or WebRequestService()
        self.dom_extractor_service = dom_extractor_service or DomExtractorService()

    @classmethod
    def from_settings(cls):
        return cls(
            web_service=WebRequestService(
                request_timeout=getattr(
                    settings, "SCRAPE_REQUEST_TIMEOUT_SECONDS", 30.0
                ),
                page_timeout_ms=getattr(settings, "SCRAPE_PAGE_TIMEOUT_MS", 30_000),
                max_html_bytes=getattr(settings, "SCRAPE_MAX_HTML_BYTES", 5_000_000),
            ),
            dom_extractor_service=DomExtractorService(
                max_depth=getattr(settings, "SCRAPE_MAX_EXTRACTION_DEPTH", 50),
                max_nodes=getattr(settings, "SCRAPE_MAX_EXTRACTION_NODES", 10_000),
                max_elements=getattr(settings, "SCRAPE_MAX_ELEMENTS", 1_000),
            ),
        )

    def scrape(self, url, class_names):
        html_content = async_to_sync(self.web_service.fetch_with_playwright)(url)
        soup = self.dom_extractor_service.parse(html_content)
        return self.dom_extractor_service.get_elements(soup, class_names)
