# Generated by Django 5.0.4 on 2024-05-15 22:51

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("play", "0013_leaderboard"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaderboard",
            name="date",
            field=models.DateField(
                default=datetime.datetime(
                    2024, 5, 15, 22, 51, 39, 537499, tzinfo=datetime.timezone.utc
                )
            ),
            preserve_default=False,
        ),
    ]
