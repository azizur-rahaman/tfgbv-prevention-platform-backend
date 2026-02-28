# Generated manually for report app

import uuid
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("evidence", "0003_rename_evidence_ev_assigne_4a8c2d_idx_evidence_ev_assigne_6d04ac_idx"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Report",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, help_text="Unique report identifier.", primary_key=True, serialize=False)),
                ("testimonial_text", models.TextField(blank=True, help_text="Written testimonial about the incident.")),
                ("testimonial_voice_path", models.CharField(blank=True, help_text="S3 path to voice testimonial file.", max_length=500)),
                ("testimonial_video_path", models.CharField(blank=True, help_text="S3 path to video testimonial file.", max_length=500)),
                ("digital_signature", models.TextField(help_text="Digital signature payload (base64 or hex) from the reporting device.")),
                ("signature_algorithm", models.CharField(blank=True, default="RSA-SHA256", help_text="Algorithm used for the signature (e.g. RSA-SHA256).", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reporter", models.ForeignKey(help_text="User who filed this report.", on_delete=django.db.models.deletion.PROTECT, related_name="incident_reports", to=settings.AUTH_USER_MODEL)),
                ("evidences", models.ManyToManyField(blank=True, help_text="Evidence records in the vault that this report references.", related_name="reports", to="evidence.evidence")),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Incident Report",
                "verbose_name_plural": "Incident Reports",
            },
        ),
    ]
