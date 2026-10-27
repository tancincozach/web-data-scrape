from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(request):
    """Liveness endpoint used by Docker and load balancers."""
    return JsonResponse({"status": "ok"})
