import requests
from .web_proxy_service import WebProxyService
from playwright.async_api import async_playwright

class WebRequestService:
    """
    A service for handling HTTP requests and JavaScript-rendered content using requests and Playwright.

    This service supports static content fetching using `requests` and JavaScript-rendered
    content fetching using `Playwright`, with optional proxy support.
    """
    
    def __init__(self, use_proxy: bool = False, proxy_service: WebProxyService = None):
        """
        Initialize the WebRequestService.

        :param use_proxy: Boolean flag to indicate whether to use a proxy.
        :param proxy_service: Instance of WebProxyService to handle proxy configuration.
        """
        self.use_proxy = use_proxy
        self.proxy_service = proxy_service

    def _get_proxy(self) -> dict:
        """
        Get proxy configuration if proxy usage is enabled.

        :return: A dictionary containing 'http' and 'https' proxy configurations, or None if no proxy is set.
        """
        return self.proxy_service.get_proxy() if self.use_proxy and self.proxy_service else None

    def fetch(self, url: str) -> str:
        """
        Fetch static content of a webpage using requests.

        :param url: The URL of the page to fetch.
        :return: The HTML content of the page as a string.
        """
        try:
            response = requests.get(url, proxies=self._get_proxy())
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.text
        except requests.RequestException as e:
            return self._handle_error(url, e)

    async def fetch_with_playwright(self, url: str, menu_selector: str = None, headless: bool = True) -> str:
        """
        Fetch JavaScript-rendered content using Playwright and optionally wait for a dynamic element.

        :param url: The URL of the page to fetch.
        :param menu_selector: The CSS selector for a dynamic element to wait for (optional).
        :param headless: Whether to run the browser in headless mode (default: True).
        :return: The fully rendered HTML content of the page as a string.
        """
        try:
            proxy = self._get_proxy()
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=headless, 
                    proxy={"server": proxy['http']} if proxy else None
                )
                page = await browser.new_page()
                await page.goto(url)

                if menu_selector:
                    # Wait for the dynamic element to load
                    await page.wait_for_selector(menu_selector)
                    await page.hover(menu_selector)  # Optionally interact with the element

                content = await page.content()
                await browser.close()
                return content
        except Exception as e:
            return self._handle_error(url, e)

    def _handle_error(self, url: str, exception: Exception) -> str:
        """
        Handle errors during fetching and log them.

        :param url: The URL that caused the error.
        :param exception: The exception that was raised.
        :return: An empty string to indicate failure.
        """
        print(f"Error fetching {url}: {exception}")
        return ""
