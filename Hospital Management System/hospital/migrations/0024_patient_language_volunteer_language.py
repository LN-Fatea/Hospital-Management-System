# Generated by Django 4.2.18 on 2025-02-02 20:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hospital", "0023_volunteer_interest_volunteer_work_history_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="language",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="volunteer",
            name="language",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
