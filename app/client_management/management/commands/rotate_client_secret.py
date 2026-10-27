from django.core.management.base import BaseCommand

from app.client_management.models import Client


class Command(BaseCommand):
    help = "Rotate a client's secret and print the new raw secret once"

    def add_arguments(self, parser):
        parser.add_argument("client_id", type=str, help="The client_id to rotate")

    def handle(self, *args, **kwargs):
        try:
            client = Client.objects.get(client_id=kwargs["client_id"])
        except Client.DoesNotExist:
            self.stderr.write(self.style.ERROR("Client not found."))
            return

        raw_secret = client.rotate_secret()
        self.stdout.write(
            self.style.SUCCESS(
                f"Rotated secret for client {client.client_id} ({client.name})."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Client Secret (raw): {raw_secret} - Save this securely; it cannot be shown again."
            )
        )
