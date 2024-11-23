from django.db import models
from django.utils.timezone import now
import secrets
from hashlib import sha256

def hash_secret(secret):
    """Hash a secret using SHA-256."""
    return sha256(secret.encode()).hexdigest()

class Client(models.Model):
    client_id = models.CharField(max_length=64, unique=True)
    client_secret = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'web_scrape_clients'  # Set the explicit table name here

    def generate_credentials(self):
        """Generate and hash a secure client ID and secret."""
        self.client_id = secrets.token_urlsafe(16)
        raw_secret = secrets.token_urlsafe(32)
        self.client_secret = hash_secret(raw_secret)
        return self.client_id, raw_secret

    def is_valid(self):
        """Check if the client is active and not expired."""
        return self.is_active and (self.expires_at is None or self.expires_at > now())

    def save(self, *args, **kwargs):
        if not self.pk:
            _, raw_secret = self.generate_credentials()
            self.raw_secret = raw_secret
        super().save(*args, **kwargs)
