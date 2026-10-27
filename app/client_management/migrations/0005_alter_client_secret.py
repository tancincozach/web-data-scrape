from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("client_management", "0004_alter_client_table"),
    ]

    operations = [
        migrations.AlterField(
            model_name="client",
            name="client_secret",
            field=models.CharField(max_length=255),
        ),
    ]
