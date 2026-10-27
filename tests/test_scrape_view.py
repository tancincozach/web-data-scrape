import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from app.scrape.scrape_data_view import WebScrapeView
from app.services.exceptions import (
    FetchError,
    FetchTimeoutError,
    ParseError,
    UnsafeUrlError,
)


class FakeScrapeService:
    def __init__(self, data=None, error=None):
        self.data = data if data is not None else []
        self.error = error
        self.calls = []

    def scrape(self, url, class_names):
        self.calls.append((url, class_names))
        if self.error:
            raise self.error
        return self.data


def make_view(service):
    return WebScrapeView(scrape_service=service)


def make_request(**params):
    return Request(APIRequestFactory().get("/scrape/data/", params))


def test_successful_scrape_returns_extracted_data():
    service = FakeScrapeService(
        data=[{"tag": "div", "text": "Hello", "attributes": {}, "children": []}]
    )

    response = make_view(service).get(
        make_request(url="https://example.com", class_name="item")
    )

    assert response.status_code == 200
    assert response.data["scraped_data"][0]["text"] == "Hello"
    assert service.calls == [("https://example.com", ["item"])]


@pytest.mark.parametrize(
    "error,expected_status",
    [
        (UnsafeUrlError("blocked"), 400),
        (FetchTimeoutError("timeout"), 504),
        (FetchError("upstream"), 502),
        (ParseError("bad html"), 502),
    ],
)
def test_scrape_errors_map_to_http_statuses(error, expected_status):
    service = FakeScrapeService(error=error)

    response = make_view(service).get(
        make_request(url="https://example.com", class_name="item")
    )

    assert response.status_code == expected_status
    assert "error" in response.data


def test_unexpected_error_is_generic_and_does_not_leak_details():
    service = FakeScrapeService(error=RuntimeError("internal secret"))

    response = make_view(service).get(
        make_request(url="https://example.com", class_name="item")
    )

    assert response.status_code == 500
    assert response.data["error"] == "An unexpected error occurred."
    assert "internal secret" not in response.data["error"]


@pytest.mark.parametrize(
    "params",
    [
        {"url": "https://example.com"},
        {"class_name": "item"},
        {"url": "not-a-url", "class_name": "item"},
        {"url": "https://example.com", "class_name": ""},
    ],
)
def test_invalid_parameters_are_rejected(params):
    service = FakeScrapeService()

    response = make_view(service).get(make_request(**params))

    assert response.status_code == 400
    assert response.data["error"] == "Invalid request parameters."
    assert service.calls == []


def test_too_many_class_names_are_rejected():
    service = FakeScrapeService()
    params = [("url", "https://example.com")] + [
        ("class_name", f"item-{index}") for index in range(51)
    ]
    request = Request(APIRequestFactory().get("/scrape/data/", params))

    response = make_view(service).get(request)

    assert response.status_code == 400
    assert service.calls == []


def test_overlong_class_name_is_rejected():
    service = FakeScrapeService()

    response = make_view(service).get(
        make_request(url="https://example.com", class_name="x" * 201)
    )

    assert response.status_code == 400
    assert service.calls == []
