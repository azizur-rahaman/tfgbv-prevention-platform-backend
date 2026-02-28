# Phase 1: Evidence assigned_upazila, verdict fields, EvidencePurgeRequest

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidence", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="evidence",
            name="assigned_upazila",
            field=models.CharField(
                blank=True,
                help_text="Upazila this evidence is assigned to. Police see only evidence for their assigned_upazila.",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="evidence",
            name="verdict",
            field=models.CharField(
                blank=True,
                choices=[
                    ("admitted", "Admitted"),
                    ("rejected", "Rejected"),
                    ("under_review", "Under Review"),
                ],
                help_text="Court disposition recorded by judiciary.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="evidence",
            name="verdict_at",
            field=models.DateTimeField(
                blank=True,
                help_text="When the verdict was recorded.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="evidence",
            name="verdict_by",
            field=models.ForeignKey(
                blank=True,
                help_text="Judiciary user who recorded the verdict.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="verdicts_recorded",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name="evidence",
            index=models.Index(fields=["assigned_upazila"], name="evidence_ev_assigne_4a8c2d_idx"),
        ),
        migrations.CreateModel(
            name="EvidencePurgeRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.TextField(blank=True, help_text="Reason for purge request.")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("denied", "Denied"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "evidence",
                    models.ForeignKey(
                        help_text="Evidence the victim wants purged.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="purge_requests",
                        to="evidence.evidence",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        help_text="User (typically victim/reporter) who requested purge.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purge_requests_made",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="BCC admin who reviewed.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="purge_requests_reviewed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Evidence Purge Request",
                "verbose_name_plural": "Evidence Purge Requests",
                "ordering": ["-created_at"],
            },
        ),
    ]
