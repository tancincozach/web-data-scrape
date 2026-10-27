from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Normalize DRF's built-in ``detail`` errors to the API error envelope."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error": str(response.data["detail"])}
    return response
