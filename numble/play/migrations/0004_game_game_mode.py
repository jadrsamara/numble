# Generated by Django 5.0.4 on 2024-05-02 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("play", "0003_rename_author_game_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="game_mode",
            field=models.CharField(
                choices=[
                    ("easy", "Easy Game Mode"),
                    ("medium", "Medium Game Mode"),
                    ("hard", "Hard Game Mode"),
                    ("daily", "Daily Numble"),
                ],
                default="easy",
                max_length=6,
            ),
        ),
    ]
