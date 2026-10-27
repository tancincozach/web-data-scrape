from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

from .models import Client


class ClientAuthentication(BaseAuthentication):
    """Authenticate API requests with ``X-Client-ID`` and ``X-Client-Secret``."""

    def authenticate(self, request):
        client_id = request.headers.get("X-Client-ID")
        client_secret = request.headers.get("X-Client-Secret")

        if not client_id or not client_secret:
            raise NotAuthenticated("Missing client credentials.")

        try:
            client = Client.objects.get(client_id=client_id)
        except Client.DoesNotExist:
            raise AuthenticationFailed("Invalid or expired client credentials.")

        if not client.is_valid() or not client.verify_secret(client_secret):
            raise AuthenticationFailed("Invalid or expired client credentials.")

        request.client = client
        return client, None

    def authenticate_header(self, request):
        return 'ClientCredentials realm="web-data-scrape"'
