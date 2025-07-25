# Generated by Django 5.1.5 on 2025-02-02 00:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hospital", "0018_auto_20201015_2036"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Volunteer",
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
                (
                    "profile_pic",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="profile_pic/VolunteerProfilePic/",
                    ),
                ),
                ("address", models.CharField(max_length=40)),
                ("mobile", models.CharField(max_length=20, null=True)),
                (
                    "department",
                    models.CharField(
                        choices=[
                            ("Cardiologist", "Cardiologist"),
                            ("Dermatologists", "Dermatologists"),
                            (
                                "Emergency Medicine Specialists",
                                "Emergency Medicine Specialists",
                            ),
                            ("Allergists/Immunologists", "Allergists/Immunologists"),
                            ("Anesthesiologists", "Anesthesiologists"),
                            ("Colon and Rectal Surgeons", "Colon and Rectal Surgeons"),
                        ],
                        default="Cardiologist",
                        max_length=50,
                    ),
                ),
                ("status", models.BooleanField(default=False)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
