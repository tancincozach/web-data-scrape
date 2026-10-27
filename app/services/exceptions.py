class ScrapeError(Exception):
    """Base class for expected scraping failures."""


class UnsafeUrlError(ScrapeError, ValueError):
    """Raised when a URL is not safe to fetch server-side."""


class FetchError(ScrapeError):
    """Raised when a remote page cannot be fetched."""


class FetchTimeoutError(FetchError):
    """Raised when fetching a remote page exceeds the allowed time."""


class ParseError(ScrapeError):
    """Raised when HTML content cannot be parsed."""
