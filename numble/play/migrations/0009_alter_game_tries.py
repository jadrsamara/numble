# Generated by Django 5.0.4 on 2024-05-02 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("play", "0008_alter_game_duration_alter_game_finish_time_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="tries",
            field=models.JSONField(default=dict),
        ),
    ]
