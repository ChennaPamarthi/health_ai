# Generated manually to add structured medical reports.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("health", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MedicalReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_type", models.CharField(choices=[("Blood Report", "Blood Report"), ("MRI", "MRI"), ("ECG", "ECG"), ("X-Ray", "X-Ray"), ("Other", "Other")], max_length=50)),
                ("report_title", models.CharField(blank=True, max_length=200)),
                ("summary", models.TextField(blank=True)),
                ("findings", models.TextField(blank=True)),
                ("recommendations", models.TextField(blank=True)),
                ("report_date", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("document", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="medical_report", to="health.medicaldocument")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="medical_reports", to="health.user")),
            ],
            options={
                "db_table": "medical_reports",
                "ordering": ["-created_at"],
            },
        ),
    ]
