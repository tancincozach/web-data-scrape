import asyncio
import logging
from typing import Callable, Optional
from urllib.parse import urljoin, urlsplit

import requests
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from .exceptions import FetchError, FetchTimeoutError, UnsafeUrlError
from .url_validator import validate_public_url
from .web_proxy_service import WebProxyService

logger = logging.getLogger(__name__)


class WebRequestService:
    """
    A service for fetching static and JavaScript-rendered web content.

    Transport concerns live here: request construction, timeouts, proxy
    selection, browser lifecycle, and URL-safety enforcement. Callers receive
    either HTML text or an explicit ``FetchError``; failures are never encoded
    as an empty string.
    """

    MAX_REDIRECTS = 5

    def __init__(
        self,
        use_proxy: bool = False,
        proxy_service: Optional[WebProxyService] = None,
        *,
        request_timeout: float = 30.0,
        page_timeout_ms: int = 30_000,
        max_html_bytes: int = 5_000_000,
        url_validator: Callable[[str], str] = validate_public_url,
        playwright_factory: Callable = async_playwright,
    ):
        self.use_proxy = use_proxy
        self.proxy_service = proxy_service
        self.request_timeout = request_timeout
        self.page_timeout_ms = page_timeout_ms
        self.max_html_bytes = max_html_bytes
        self._url_validator = url_validator
        self._playwright_factory = playwright_factory

    def _get_proxy(self) -> Optional[dict]:
        """Return the proxy configuration, or ``None`` when not configured."""
        return (
            self.proxy_service.get_proxy()
            if self.use_proxy and self.proxy_service
            else None
        )

    def _ensure_size(self, content: str, url: str) -> None:
        if len(content.encode("utf-8")) > self.max_html_bytes:
            raise FetchError(
                f"Response from {self._describe(url)} exceeded the size limit."
            )

    @staticmethod
    def _describe(url: str) -> str:
        try:
            return urlsplit(url).hostname or "the target"
        except ValueError:
            return "the target"

    def fetch(self, url: str) -> str:
        """Fetch a static page with ``requests``.

        :raises UnsafeUrlError: if the URL is not a safe public HTTP(S) target.
        :raises FetchTimeoutError: if the request times out.
        :raises FetchError: for other transport failures or oversized responses.
        """
        current_url = url
        try:
            for _ in range(self.MAX_REDIRECTS + 1):
                self._url_validator(current_url)
                response = requests.get(
                    current_url,
                    proxies=self._get_proxy(),
                    timeout=self.request_timeout,
                    allow_redirects=False,
                )
                if response.is_redirect:
                    location = response.headers.get("Location")
                    if not location:
                        raise FetchError(
                            f"Redirect from {self._describe(current_url)} had no location."
                        )
                    current_url = urljoin(current_url, location)
                    continue

                response.raise_for_status()
                content = response.text
                self._ensure_size(content, url)
                return content
        except requests.Timeout as exc:
            raise FetchTimeoutError(
                f"Timed out fetching {self._describe(current_url)}."
            ) from exc
        except requests.RequestException as exc:
            raise FetchError(f"Unable to fetch {self._describe(current_url)}.") from exc

        raise FetchError(f"Too many redirects while fetching {self._describe(url)}.")

    async def fetch_with_playwright(
        self,
        url: str,
        menu_selector: Optional[str] = None,
        headless: bool = True,
    ) -> str:
        """Fetch the fully rendered HTML for a JavaScript-heavy page.

        Every navigation and subresource request is checked against the URL
        validator before it is allowed to proceed. This blocks redirects and
        page subresources that point at private or otherwise unsafe addresses.

        :raises UnsafeUrlError: if the target or one of its requests is unsafe.
        :raises FetchTimeoutError: if navigation or a selector wait times out.
        :raises FetchError: for other browser/transport failures or oversized HTML.
        """
        self._url_validator(url)
        try:
            return await self._fetch_rendered(url, menu_selector, headless)
        except (UnsafeUrlError, FetchError):
            raise
        except PlaywrightTimeoutError as exc:
            raise FetchTimeoutError(
                f"Timed out fetching {self._describe(url)}."
            ) from exc
        except asyncio.TimeoutError as exc:
            raise FetchTimeoutError(
                f"Timed out fetching {self._describe(url)}."
            ) from exc
        except Exception as exc:
            raise FetchError(f"Unable to fetch {self._describe(url)}.") from exc

    async def _fetch_rendered(
        self,
        url: str,
        menu_selector: Optional[str],
        headless: bool,
    ) -> str:
        proxy = self._get_proxy()
        blocked_urls = []
        validated_hosts = set()

        async def guard_request(route) -> None:
            request = route.request
            request_url = request.url
            try:
                parsed = urlsplit(request_url)
                if parsed.scheme.lower() not in {"http", "https"}:
                    if request.is_navigation_request():
                        blocked_urls.append(request_url)
                        await route.abort("blockedbyclient")
                        return
                    await route.continue_()
                    return

                host_key = (parsed.scheme.lower(), parsed.netloc.lower())
                if host_key not in validated_hosts:
                    await asyncio.to_thread(self._url_validator, request_url)
                    validated_hosts.add(host_key)
            except UnsafeUrlError:
                blocked_urls.append(request_url)
                await route.abort("blockedbyclient")
                return

            await route.continue_()

        async with self._playwright_factory() as playwright:
            browser = await playwright.chromium.launch(
                headless=headless,
                proxy={"server": proxy["http"]} if proxy else None,
            )
            try:
                page = await browser.new_page()
                await page.route("**/*", guard_request)
                try:
                    await page.goto(url, timeout=self.page_timeout_ms)
                except Exception:
                    if blocked_urls:
                        raise UnsafeUrlError(
                            f"Blocked unsafe request to {self._describe(blocked_urls[0])}."
                        )
                    raise

                if blocked_urls:
                    raise UnsafeUrlError(
                        f"Blocked unsafe request to {self._describe(blocked_urls[0])}."
                    )

                if menu_selector:
                    await page.wait_for_selector(
                        menu_selector, timeout=self.page_timeout_ms
                    )
                    await page.hover(menu_selector)

                final_url = page.url
                self._url_validator(final_url)

                content = await page.content()
                self._ensure_size(content, url)
                return content
            finally:
                try:
                    await browser.close()
                except Exception:
                    logger.exception("Failed to close Playwright browser.")
