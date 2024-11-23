from django.core.management.base import BaseCommand
from app.client_management.models import hash_secret, Client
from datetime import datetime

class Command(BaseCommand):
    help = 'Create a new client and generate credentials (client_id and client_secret)'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help="The name of the client")
        parser.add_argument('is_active', type=bool, help="Whether the client is active")
        parser.add_argument('expires_at', type=str, help="Expiration date in YYYY-MM-DD format (Leave empty for no expiration)", nargs='?')

    def handle(self, *args, **kwargs):
        name = kwargs['name']
        is_active = kwargs['is_active']
        expires_at = kwargs.get('expires_at', None)
        
        if expires_at:
            try:
                expires_at = datetime.strptime(expires_at, '%Y-%m-%d')
            except ValueError:
                self.stdout.write(self.style.ERROR("Invalid date format. Use YYYY-MM-DD."))
                return
        else:
            expires_at = None

        client = Client(name=name, is_active=is_active, expires_at=expires_at)

        client_id, raw_secret = client.generate_credentials()
        client.client_id = client_id
        client.client_secret = hash_secret(raw_secret)
        client.save()

        self.stdout.write(self.style.SUCCESS(f"Successfully created client {name} with client_id: {client_id}"))
        self.stdout.write(self.style.SUCCESS(f"Client Secret (raw): {raw_secret} - Save this securely"))
