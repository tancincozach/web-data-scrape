from datetime import timedelta

import pytest
from django.core.cache import cache
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.request import Request

from app.client_management.authentication import ClientAuthentication
from app.client_management.models import Client
from app.client_management.permissions import IsClient
from app.client_management.throttling import ClientRateThrottle

pytestmark = pytest.mark.django_db


def make_request(client_id=None, client_secret=None):
    headers = {}
    if client_id:
        headers["X-Client-ID"] = client_id
    if client_secret:
        headers["X-Client-Secret"] = client_secret
    return Request(RequestFactory().get("/scrape/data/", headers=headers))


def test_valid_credentials_authenticate():
    client, raw_secret = Client.issue_credentials(name="Acme")
    request = make_request(client.client_id, raw_secret)

    authenticated_client, auth = ClientAuthentication().authenticate(request)

    assert authenticated_client.pk == client.pk
    assert auth is None
    assert request.client.pk == client.pk


def test_missing_credentials_are_not_authenticated():
    with pytest.raises(NotAuthenticated):
        ClientAuthentication().authenticate(make_request())


def test_wrong_secret_is_rejected():
    client, _ = Client.issue_credentials(name="Acme")

    with pytest.raises(AuthenticationFailed):
        ClientAuthentication().authenticate(
            make_request(client.client_id, "wrong-secret")
        )


def test_unknown_client_is_rejected():
    with pytest.raises(AuthenticationFailed):
        ClientAuthentication().authenticate(make_request("unknown", "secret"))


def test_inactive_and_expired_clients_are_rejected():
    inactive, inactive_secret = Client.issue_credentials(
        name="Inactive", is_active=False
    )
    expired, expired_secret = Client.issue_credentials(
        name="Expired", expires_at=timezone.now() - timedelta(seconds=1)
    )

    with pytest.raises(AuthenticationFailed):
        ClientAuthentication().authenticate(
            make_request(inactive.client_id, inactive_secret)
        )
    with pytest.raises(AuthenticationFailed):
        ClientAuthentication().authenticate(
            make_request(expired.client_id, expired_secret)
        )


def test_authentication_header_is_client_credentials():
    assert (
        ClientAuthentication().authenticate_header(None).startswith("ClientCredentials")
    )


def test_permission_accepts_only_client_users():
    client, _ = Client.issue_credentials(name="Acme")
    request = make_request(client.client_id, "secret")
    request.user = client

    assert IsClient().has_permission(request, None) is True


def test_throttle_uses_the_client_identity():
    client = Client(pk=123, client_id="client-id", name="Acme")
    request = Request(RequestFactory().get("/scrape/data/"))
    request.user = client

    throttle = ClientRateThrottle()
    throttle.rate = "1/min"
    throttle.num_requests = 1
    throttle.duration = 60
    cache.clear()

    assert throttle.allow_request(request, None) is True
    assert throttle.allow_request(request, None) is False
