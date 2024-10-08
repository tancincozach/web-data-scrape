class WebProxyService:
    def __init__(self, proxy=None):
        """
        Initialize the proxy service with an optional proxy URL.
        
        :param proxy: A proxy URL in the format 'http://username:password@host:port' (optional).
        """
        self.proxy = proxy

    def get_proxy(self) -> dict:
        """
        Return the proxy configuration as a dictionary if a proxy is set.

        :return: Dictionary with 'http' and 'https' proxies, or None if no proxy is set.
        """
        return {'http': self.proxy, 'https': self.proxy} if self.proxy else None
