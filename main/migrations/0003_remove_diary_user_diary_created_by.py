# Generated by Django 5.1.5 on 2025-01-30 12:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_alter_task_options_remove_project_updated_at_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="diary",
            name="user",
        ),
        migrations.AddField(
            model_name="diary",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_diary_entries",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
