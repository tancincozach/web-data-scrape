from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import requests
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.services.exceptions import FetchError, FetchTimeoutError, UnsafeUrlError
from app.services.web_request_service import WebRequestService


class FakePage:
    def __init__(
        self, content="<html>rendered</html>", goto_error=None, goto_handler=None
    ):
        self.content_value = content
        self.goto_error = goto_error
        self.goto_handler = goto_handler
        self.url = "https://example.com/final"
        self.route_handler = None
        self.goto_timeout = None

    async def route(self, pattern, handler):
        self.route_handler = handler

    async def goto(self, url, timeout=None):
        self.goto_timeout = timeout
        if self.goto_handler:
            await self.goto_handler(self)
        if self.goto_error:
            raise self.goto_error

    async def wait_for_selector(self, selector, timeout=None):
        return None

    async def hover(self, selector):
        return None

    async def content(self):
        return self.content_value


class FakeBrowser:
    def __init__(self, page):
        self.page = page
        self.closed = False
        self.launch_kwargs = None

    async def new_page(self):
        return self.page

    async def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self, browser):
        self.browser = browser

    async def launch(self, **kwargs):
        self.browser.launch_kwargs = kwargs
        return self.browser


class FakePlaywright:
    def __init__(self, browser):
        self.chromium = FakeChromium(browser)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_service(browser, **kwargs):
    return WebRequestService(
        url_validator=lambda url: url,
        playwright_factory=lambda: FakePlaywright(browser),
        **kwargs,
    )


async def test_playwright_success_closes_browser_and_sets_timeout():
    page = FakePage()
    browser = FakeBrowser(page)
    service = make_service(browser, page_timeout_ms=1234)

    content = await service.fetch_with_playwright("https://example.com")

    assert content == "<html>rendered</html>"
    assert browser.closed is True
    assert page.goto_timeout == 1234


async def test_playwright_error_closes_browser_and_raises_fetch_error():
    page = FakePage(goto_error=RuntimeError("navigation failed"))
    browser = FakeBrowser(page)
    service = make_service(browser)

    with pytest.raises(FetchError):
        await service.fetch_with_playwright("https://example.com")

    assert browser.closed is True


async def test_playwright_timeout_maps_to_fetch_timeout():
    page = FakePage(goto_error=PlaywrightTimeoutError("timed out"))
    browser = FakeBrowser(page)
    service = make_service(browser)

    with pytest.raises(FetchTimeoutError):
        await service.fetch_with_playwright("https://example.com")

    assert browser.closed is True


class FakeRoute:
    def __init__(self, request_url, is_navigation=True):
        self.request = SimpleNamespace(
            url=request_url,
            is_navigation_request=lambda: is_navigation,
        )
        self.aborted_with = None
        self.continued = False

    async def abort(self, error_code):
        self.aborted_with = error_code

    async def continue_(self):
        self.continued = True


async def test_unsafe_navigation_redirect_is_blocked_and_closes_browser():
    def reject_private(url):
        if "169.254.169.254" in url:
            raise UnsafeUrlError("private")
        return url

    async def navigation(page):
        route = FakeRoute("http://169.254.169.254/latest/meta-data/")
        await page.route_handler(route)
        assert route.aborted_with == "blockedbyclient"
        raise RuntimeError("net::ERR_BLOCKED_BY_CLIENT")

    page = FakePage(goto_handler=navigation)
    browser = FakeBrowser(page)
    service = WebRequestService(
        url_validator=reject_private,
        playwright_factory=lambda: FakePlaywright(browser),
    )

    with pytest.raises(UnsafeUrlError):
        await service.fetch_with_playwright("https://example.com")

    assert browser.closed is True


async def test_public_navigation_is_allowed_through_route_guard():
    def allow_public(url):
        if "169.254.169.254" in url:
            raise UnsafeUrlError("private")
        return url

    observed = {}

    async def navigation(page):
        route = FakeRoute("https://example.com/page")
        await page.route_handler(route)
        observed["continued"] = route.continued

    page = FakePage(goto_handler=navigation)
    browser = FakeBrowser(page)
    service = WebRequestService(
        url_validator=allow_public,
        playwright_factory=lambda: FakePlaywright(browser),
    )

    content = await service.fetch_with_playwright("https://example.com")

    assert content == "<html>rendered</html>"
    assert observed["continued"] is True
    assert browser.closed is True


async def test_playwright_rejects_unsafe_target_before_launch():
    def reject(url):
        raise UnsafeUrlError("blocked")

    def unexpected_factory():
        raise AssertionError("browser should not be launched")

    service = WebRequestService(
        url_validator=reject,
        playwright_factory=unexpected_factory,
    )

    with pytest.raises(UnsafeUrlError):
        await service.fetch_with_playwright("http://127.0.0.1/")


async def test_playwright_rejects_oversized_content():
    page = FakePage(content="x" * 20)
    browser = FakeBrowser(page)
    service = make_service(browser, max_html_bytes=10)

    with pytest.raises(FetchError):
        await service.fetch_with_playwright("https://example.com")

    assert browser.closed is True


def test_static_fetch_passes_timeout_and_returns_text():
    response = Mock()
    response.is_redirect = False
    response.text = "<html>static</html>"
    response.raise_for_status = Mock()
    with patch(
        "app.services.web_request_service.requests.get", return_value=response
    ) as get:
        service = WebRequestService(url_validator=lambda url: url, request_timeout=7)

        assert service.fetch("https://example.com") == "<html>static</html>"
        get.assert_called_once_with(
            "https://example.com",
            proxies=None,
            timeout=7,
            allow_redirects=False,
        )


def test_static_fetch_validates_each_redirect_target():
    redirect = Mock()
    redirect.is_redirect = True
    redirect.headers = {"Location": "http://127.0.0.1/internal"}
    final = Mock()
    final.is_redirect = False
    final.text = "<html>ok</html>"
    final.raise_for_status = Mock()

    def validator(url):
        if "127.0.0.1" in url:
            raise UnsafeUrlError("private")
        return url

    with patch(
        "app.services.web_request_service.requests.get",
        side_effect=[redirect, final],
    ):
        service = WebRequestService(url_validator=validator)

        with pytest.raises(UnsafeUrlError):
            service.fetch("https://example.com")


def test_static_fetch_timeout_raises_fetch_timeout():
    with patch(
        "app.services.web_request_service.requests.get",
        side_effect=requests.Timeout("slow"),
    ):
        service = WebRequestService(url_validator=lambda url: url)

        with pytest.raises(FetchTimeoutError):
            service.fetch("https://example.com")


def test_static_fetch_http_error_raises_fetch_error():
    with patch(
        "app.services.web_request_service.requests.get",
        side_effect=requests.RequestException("bad"),
    ):
        service = WebRequestService(url_validator=lambda url: url)

        with pytest.raises(FetchError):
            service.fetch("https://example.com")


def test_static_fetch_rejects_oversized_content():
    response = Mock()
    response.is_redirect = False
    response.text = "x" * 11
    response.raise_for_status = Mock()
    with patch("app.services.web_request_service.requests.get", return_value=response):
        service = WebRequestService(url_validator=lambda url: url, max_html_bytes=10)

        with pytest.raises(FetchError):
            service.fetch("https://example.com")
