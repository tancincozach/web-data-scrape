import logging
from django.urls import get_resolver, Resolver404
from django.http import HttpResponseForbidden
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

def get_all_routes():
    """
    Recursively retrieves all URL patterns in the project and returns them as a list of strings.
    """
    url_patterns = get_resolver().url_patterns
    routes = []

    def extract_routes(patterns, parent_pattern=''):
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):
                # If pattern has nested url_patterns, recursively extract them
                extract_routes(pattern.url_patterns, parent_pattern + str(pattern.pattern))
            else:
                # Append the full route pattern to the list
                routes.append(parent_pattern + str(pattern.pattern))
    
    try:
        extract_routes(url_patterns)
    except Resolver404:
        logger.error("URL resolver not found.")
    
    logger.debug(f"All routes: {routes}")
    return routes

class DynamicRouteGuardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.routes = get_all_routes()
        self.excluded_routes = ['/api/login', '/api/token/refresh', '/api/logout']
        logger.debug(f"Initialized DynamicRouteGuardMiddleware with routes: {self.routes}")

    def __call__(self, request):
        logger.debug(f"Request path: {request.path}")

        if request.path.startswith('/api/') and not any(request.path.startswith(excluded_route) for excluded_route in self.excluded_routes):
            logger.debug(f"Path requires authentication: {request.path}")
            jwt_auth = JWTAuthentication()
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    # Extract token from header
                    prefix, token = auth_header.split(' ')
                    if prefix == 'Bearer':
                        logger.debug(f"Token extracted: {token}")
                        # Verify token
                        validated_token = jwt_auth.get_validated_token(token)
                        request.user = jwt_auth.get_user(validated_token)
                        logger.debug(f"User authenticated: {request.user}")
                        if not request.user.is_authenticated:
                            logger.warning("User is not authenticated.")
                            return HttpResponseForbidden('You do not have permission to access this resource.')
                except Exception as e:
                    logger.error(f"Token validation error: {e}")
                    return HttpResponseForbidden('You do not have permission to access this resource.')

        response = self.get_response(request)
        logger.debug(f"Response status: {response.status_code}")
        return response
