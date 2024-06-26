# Generated by Django 5.0.4 on 2024-05-02 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("play", "0006_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="tries",
            field=models.JSONField(default={}),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="game",
            name="game_mode",
            field=models.CharField(
                choices=[
                    ("easy", "Easy Game Mode"),
                    ("medium", "Medium Game Mode"),
                    ("hard", "Hard Game Mode"),
                    ("daily", "Daily Numble"),
                ],
                max_length=6,
            ),
        ),
    ]
