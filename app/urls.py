from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from app.api_docs import scalar_docs

urlpatterns = [
    path("scrape/", include("app.scrape.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", scalar_docs, name="scalar-docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
