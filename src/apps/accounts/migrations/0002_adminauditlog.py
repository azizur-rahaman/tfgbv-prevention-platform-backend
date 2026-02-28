# Phase 1: AdminAuditLog for BCC admin action audit

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminAuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "actor_user_id",
                    models.CharField(
                        help_text="UUID of the BCC admin who performed the action.",
                        max_length=36,
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("user_created", "User Created"),
                            ("user_deactivated", "User Deactivated"),
                            ("user_activated", "User Activated"),
                            ("role_changed", "Role Changed"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "target_user_id",
                    models.CharField(
                        blank=True,
                        help_text="UUID of the user who was created/deactivated/edited.",
                        max_length=36,
                        null=True,
                    ),
                ),
                (
                    "extra",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Extra context e.g. old_role, new_role.",
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Admin Audit Log",
                "verbose_name_plural": "Admin Audit Logs",
                "ordering": ["-timestamp"],
            },
        ),
    ]
