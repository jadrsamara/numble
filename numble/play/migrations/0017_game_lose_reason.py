# Generated by Django 5.0.4 on 2024-06-12 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("play", "0016_alter_game_game_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="lose_reason",
            field=models.CharField(max_length=256, null=True),
        ),
    ]