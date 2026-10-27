from argparse import ArgumentTypeError
from datetime import datetime, time

from django.core.management.base import BaseCommand
from django.utils import timezone

from app.client_management.models import Client


def parse_bool(value):
    """Parse a command-line boolean without ``bool('False') == True`` surprises."""
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ArgumentTypeError("Expected one of: true, false, 1, 0, yes, no, on, off.")


class Command(BaseCommand):
    help = "Create a new client and generate credentials (client_id and client_secret)"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="The name of the client")
        parser.add_argument(
            "is_active",
            nargs="?",
            default=True,
            type=parse_bool,
            help="Whether the client is active (default: true)",
        )
        parser.add_argument(
            "expires_at",
            type=str,
            help="Expiration date in YYYY-MM-DD format (leave empty for no expiration)",
            nargs="?",
        )

    def handle(self, *args, **kwargs):
        name = kwargs["name"]
        is_active = kwargs["is_active"]
        expires_at = kwargs.get("expires_at")

        if expires_at:
            try:
                expiry_date = datetime.strptime(expires_at, "%Y-%m-%d").date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR("Invalid date format. Use YYYY-MM-DD.")
                )
                return
            expires_at = timezone.make_aware(datetime.combine(expiry_date, time.min))
        else:
            expires_at = None

        client, raw_secret = Client.issue_credentials(
            name=name,
            is_active=is_active,
            expires_at=expires_at,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created client {name} with client_id: {client.client_id}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Client Secret (raw): {raw_secret} - Save this securely; it cannot be shown again."
            )
        )
