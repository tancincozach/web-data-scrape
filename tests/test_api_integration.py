from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from app.client_management.models import Client
from app.client_management.throttling import ClientRateThrottle

pytestmark = pytest.mark.django_db


class FakeScrapeService:
    def scrape(self, url, class_names):
        return [{"tag": "div", "text": "ok", "attributes": {}, "children": []}]


def auth_headers(client, raw_secret):
    return {
        "HTTP_X_CLIENT_ID": client.client_id,
        "HTTP_X_CLIENT_SECRET": raw_secret,
    }


def test_missing_credentials_are_rejected():
    response = APIClient().get(
        "/scrape/data/",
        {"url": "https://example.com", "class_name": "item"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Missing client credentials."


def test_wrong_credentials_are_rejected():
    client, _ = Client.issue_credentials(name="Acme")

    response = APIClient().get(
        "/scrape/data/",
        {"url": "https://example.com", "class_name": "item"},
        **auth_headers(client, "wrong-secret"),
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid or expired client credentials."


@patch("app.scrape.scrape_data_view.ScrapeService")
def test_valid_credentials_reach_the_scrape_service(mock_service):
    mock_service.from_settings.return_value = FakeScrapeService()
    client, raw_secret = Client.issue_credentials(name="Acme")

    response = APIClient().get(
        "/scrape/data/",
        {"url": "https://example.com", "class_name": "item"},
        **auth_headers(client, raw_secret),
    )

    assert response.status_code == 200
    assert response.json()["scraped_data"][0]["text"] == "ok"


@patch("app.scrape.scrape_data_view.ScrapeService")
def test_invalid_request_parameters_are_rejected_before_scraping(mock_service):
    scrape_service = FakeScrapeService()
    scrape_service.scrape = lambda url, class_names: pytest.fail(
        "scrape should not be called"
    )
    mock_service.from_settings.return_value = scrape_service
    client, raw_secret = Client.issue_credentials(name="Acme")

    response = APIClient().get(
        "/scrape/data/",
        {"url": "https://example.com"},
        **auth_headers(client, raw_secret),
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid request parameters."


def test_rate_limit_returns_429_after_the_client_quota():
    cache.clear()
    client, raw_secret = Client.issue_credentials(name="Acme")
    headers = auth_headers(client, raw_secret)

    with patch("app.scrape.scrape_data_view.ScrapeService") as mock_service:
        mock_service.from_settings.return_value = FakeScrapeService()
        with patch.object(ClientRateThrottle, "get_rate", return_value="2/min"):
            responses = [
                APIClient().get(
                    "/scrape/data/",
                    {"url": "https://example.com", "class_name": "item"},
                    **headers,
                )
                for _ in range(3)
            ]

    assert [response.status_code for response in responses] == [200, 200, 429]
    assert "throttled" in responses[2].json()["error"].lower()
