from django.http import JsonResponse
from hashlib import sha256
from app.client_management.models import Client
from django.utils.timezone import now

class ClientAuthenticationMiddleware:
    """
    Middleware for authenticating requests using client_id and client_secret.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_id = request.headers.get('X-Client-ID')
        client_secret = request.headers.get('X-Client-Secret')

        if not client_id or not client_secret:
            return JsonResponse({"detail": "Missing client credentials."}, status=400)

        try:
    
            client = Client.objects.get(client_id=client_id)

            if not client.is_active or (client.expires_at and client.expires_at <= now()):
                return JsonResponse({"detail": "Client credentials are inactive or expired."}, status=401)

            request.client = client

        except Client.DoesNotExist:
            return JsonResponse({"detail": "Client not found."}, status=401)

        response = self.get_response(request)

        return response
