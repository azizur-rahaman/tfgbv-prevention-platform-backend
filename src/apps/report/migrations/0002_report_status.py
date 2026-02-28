# Report workflow: pending_police → forwarded_to_judiciary

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("report", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending_police", "Pending Police Confirmation"),
                    ("forwarded_to_judiciary", "Forwarded to Judiciary"),
                ],
                default="pending_police",
                help_text="Workflow: pending_police → police confirm → forwarded_to_judiciary.",
                max_length=30,
            ),
        ),
    ]
