from django.core.management.commands.migrate import Command as MigrateCommand


class Command(MigrateCommand):
    def handle(self, *args, **options):
        exclude_apps = ["auth", "contenttypes"]
        all_apps = self.loader.migrated_apps
        apps_to_migrate = [app for app in all_apps if app not in exclude_apps]

        for app in apps_to_migrate:
            super().migrate(app, **options)
