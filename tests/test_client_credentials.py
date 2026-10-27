import hashlib
import re
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from app.client_management.models import Client

pytestmark = pytest.mark.django_db


def test_issue_credentials_stores_only_a_hash():
    client, raw_secret = Client.issue_credentials(name="Acme")

    stored = Client.objects.get(pk=client.pk)
    assert stored.client_id == client.client_id
    assert stored.client_secret != raw_secret
    assert raw_secret not in stored.client_secret
    assert stored.verify_secret(raw_secret) is True
    assert stored.verify_secret("wrong-secret") is False


def test_saving_an_existing_client_does_not_rotate_credentials():
    client, raw_secret = Client.issue_credentials(name="Acme")
    client_id = client.client_id
    stored_secret = client.client_secret

    client.save()
    client.refresh_from_db()

    assert client.client_id == client_id
    assert client.client_secret == stored_secret
    assert client.verify_secret(raw_secret) is True


def test_legacy_sha256_secret_is_upgraded_on_successful_verification():
    raw_secret = "legacy-secret"
    client = Client.objects.create(
        name="Legacy",
        client_id="legacy-client-id",
        client_secret=hashlib.sha256(raw_secret.encode()).hexdigest(),
    )

    assert client.verify_secret("wrong-secret") is False
    assert client.verify_secret(raw_secret) is True

    client.refresh_from_db()
    assert len(client.client_secret) != 64
    assert client.verify_secret(raw_secret) is True


def test_invalid_stored_hash_does_not_authenticate():
    client = Client.objects.create(
        name="Broken",
        client_id="broken-client-id",
        client_secret="not-a-supported-hash",
    )

    assert client.verify_secret("anything") is False


def test_expired_or_inactive_client_is_not_valid():
    expired, _ = Client.issue_credentials(
        name="Expired",
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    inactive, _ = Client.issue_credentials(name="Inactive", is_active=False)

    assert expired.is_valid() is False
    assert inactive.is_valid() is False


def test_create_client_command_prints_credentials_that_authenticate():
    output = StringIO()
    call_command(
        "create_client", "Command Client", "false", "2030-01-01", stdout=output
    )
    command_output = output.getvalue()

    client_id = re.search(r"client_id: (\S+)", command_output).group(1)
    raw_secret = re.search(r"Client Secret \(raw\): (\S+)", command_output).group(1)

    client = Client.objects.get(client_id=client_id)
    assert client.is_active is False
    assert client.expires_at is not None
    assert timezone.is_aware(client.expires_at)
    assert client.verify_secret(raw_secret) is True


def test_create_client_command_rejects_invalid_boolean():
    with pytest.raises(CommandError):
        call_command("create_client", "Bad Bool", "sometimes")


def test_rotate_client_secret_command_replaces_the_secret():
    client, old_secret = Client.issue_credentials(name="Rotate Me")
    output = StringIO()
    call_command("rotate_client_secret", client.client_id, stdout=output)

    new_secret = re.search(r"Client Secret \(raw\): (\S+)", output.getvalue()).group(1)
    client.refresh_from_db()

    assert new_secret != old_secret
    assert client.verify_secret(new_secret) is True
    assert client.verify_secret(old_secret) is False


def test_rotate_client_secret_command_handles_unknown_client():
    output = StringIO()
    call_command("rotate_client_secret", "missing-client", stderr=output)

    assert "Client not found." in output.getvalue()
