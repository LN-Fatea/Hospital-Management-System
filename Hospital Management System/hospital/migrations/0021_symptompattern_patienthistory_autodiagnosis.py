# Generated by Django 5.1.5 on 2025-02-02 00:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hospital", "0020_volunteerschedule_volunteertask"),
    ]

    operations = [
        migrations.CreateModel(
            name="SymptomPattern",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "symptoms",
                    models.TextField(help_text="Comma-separated list of symptoms"),
                ),
                ("possible_diagnosis", models.TextField()),
                ("recommended_tests", models.TextField(blank=True)),
                (
                    "severity_level",
                    models.IntegerField(
                        choices=[
                            (1, "Low"),
                            (2, "Medium"),
                            (3, "High"),
                            (4, "Critical"),
                        ]
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-severity_level", "name"],
            },
        ),
        migrations.CreateModel(
            name="PatientHistory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(auto_now_add=True)),
                ("symptoms", models.TextField()),
                ("diagnosis", models.TextField()),
                ("treatment", models.TextField()),
                (
                    "doctor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="hospital.doctor",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hospital.patient",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AutoDiagnosis",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("match_percentage", models.FloatField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_by_doctor", models.BooleanField(default=False)),
                ("doctor_notes", models.TextField(blank=True)),
                ("confirmed_diagnosis", models.BooleanField(default=False)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hospital.patient",
                    ),
                ),
                (
                    "symptom_pattern",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="hospital.symptompattern",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Auto Diagnoses",
                "ordering": ["-created_at"],
            },
        ),
    ]
