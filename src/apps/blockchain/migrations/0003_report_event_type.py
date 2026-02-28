# Generated manually: REPORT event type and report FK

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("report", "0001_initial"),
        ("blockchain", "0002_alter_forensiclog_event_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="forensiclog",
            name="report",
            field=models.ForeignKey(
                blank=True,
                help_text="The incident report this block is sealing.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="blockchain_logs",
                to="report.report",
            ),
        ),
        migrations.AlterField(
            model_name="forensiclog",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("capture", "Initial Capture"),
                    ("vault_ingest", "Vault Ingestion"),
                    ("access", "Evidence Accessed"),
                    ("verification", "Hash Verified"),
                    ("transfer", "Transferred to Court"),
                    ("verdict", "Verdict Recorded"),
                    ("report", "Report Filed"),
                    ("genesis", "Genesis Block"),
                ],
                default="capture",
                max_length=20,
            ),
        ),
    ]
