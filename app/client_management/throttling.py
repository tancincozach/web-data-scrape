from rest_framework.throttling import SimpleRateThrottle

from .models import Client


class ClientRateThrottle(SimpleRateThrottle):
    """Rate-limit requests per authenticated client."""

    scope = "scrape"

    def get_cache_key(self, request, view):
        if not isinstance(request.user, Client):
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": request.user.pk,
        }
