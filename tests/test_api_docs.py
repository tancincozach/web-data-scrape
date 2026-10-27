from django.urls import reverse
from rest_framework.test import APIClient


def test_scalar_docs_page_points_at_schema_and_pinned_asset():
    response = APIClient().get(reverse("scalar-docs"))

    assert response.status_code == 200
    body = response.content.decode()
    assert "createApiReference" in body
    assert "/api/schema/" in body
    assert "@scalar/api-reference@1.76.0" in body


def test_openapi_schema_describes_the_scrape_endpoint_and_auth_headers():
    response = APIClient().get(reverse("api-schema"), HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    schema = response.json()
    operation = schema["paths"]["/scrape/data/"]["get"]
    parameters = {parameter["name"] for parameter in operation["parameters"]}

    assert {"url", "class_name"} <= parameters
    assert operation["security"] == [{"clientId": [], "clientSecret": []}]
    assert schema["components"]["securitySchemes"]["clientId"]["name"] == (
        "X-Client-ID"
    )
    assert schema["components"]["securitySchemes"]["clientSecret"]["name"] == (
        "X-Client-Secret"
    )
