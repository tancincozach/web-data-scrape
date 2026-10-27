from app.scrape.services import ScrapeService
from app.services.dom_extractor_service import DomExtractorService


class FakeWebService:
    def __init__(self, html='<div class="item"><span>Hello</span></div>'):
        self.html = html
        self.urls = []

    async def fetch_with_playwright(self, url):
        self.urls.append(url)
        return self.html


def test_scrape_orchestrates_fetch_parse_and_extract():
    web_service = FakeWebService()
    service = ScrapeService(
        web_service=web_service,
        dom_extractor_service=DomExtractorService(),
    )

    data = service.scrape("https://example.com", ["item"])

    assert web_service.urls == ["https://example.com"]
    assert data[0]["tag"] == "div"
    assert data[0]["children"][0]["text"] == "Hello"
