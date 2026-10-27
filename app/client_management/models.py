import hashlib
import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


def _legacy_hash_secret(secret):
    """Hash a legacy SHA-256 secret for upgrade/verification only."""
    return hashlib.sha256(secret.encode()).hexdigest()


class Client(models.Model):
    client_id = models.CharField(max_length=64, unique=True)
    client_secret = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "web_scrape_clients"

    @classmethod
    def issue_credentials(cls, *, name, is_active=True, expires_at=None):
        """Create a client and return ``(client, raw_secret)`` exactly once.

        The raw secret is never stored. Callers must show it to the operator
        immediately and discard it.
        """
        client = cls(name=name, is_active=is_active, expires_at=expires_at)
        client.client_id = secrets.token_urlsafe(16)
        raw_secret = client.rotate_secret()
        client.save()
        return client, raw_secret

    def rotate_secret(self):
        """Replace the stored secret and return the new raw secret once."""
        raw_secret = secrets.token_urlsafe(32)
        self.client_secret = make_password(raw_secret)
        if self.pk:
            self.save(update_fields=["client_secret"])
        return raw_secret

    def verify_secret(self, raw_secret) -> bool:
        """Verify a raw secret, upgrading legacy SHA-256 hashes on success."""
        if not raw_secret or not self.client_secret:
            return False

        stored = self.client_secret
        is_legacy_sha256 = len(stored) == 64 and all(
            character in "0123456789abcdefABCDEF" for character in stored
        )
        if is_legacy_sha256:
            if secrets.compare_digest(stored.lower(), _legacy_hash_secret(raw_secret)):
                self.client_secret = make_password(raw_secret)
                self.save(update_fields=["client_secret"])
                return True
            return False

        try:
            return check_password(raw_secret, stored)
        except (TypeError, ValueError):
            # A malformed or unsupported stored hash must not authenticate.
            return False

    def is_valid(self) -> bool:
        """Check if the client is active and not expired."""
        return self.is_active and (
            self.expires_at is None or self.expires_at > timezone.now()
        )
