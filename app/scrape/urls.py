# app/scrape/urls.py

from django.urls import path
from .scrape_view import WebScrapeView

urlpatterns = [
    path('', WebScrapeView.as_view(), name='web-scrape'),
    path('scrape/google/', WebScrapeView.as_view(), name='google-search'),  # New path for Google search
]
