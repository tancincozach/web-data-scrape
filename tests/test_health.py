from rest_framework.test import APIClient


def test_healthz_is_public_and_reports_ok():
    response = APIClient().get("/healthz/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_healthz_rejects_non_get_methods():
    response = APIClient().post("/healthz/")

    assert response.status_code == 405
