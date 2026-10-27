from django.urls import path
from .scrape_data_view import WebScrapeView

urlpatterns = [
    path("data/", WebScrapeView.as_view(), name="web-scrape"),
]
