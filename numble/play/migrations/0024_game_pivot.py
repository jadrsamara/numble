# Generated by Django 5.0.4 on 2024-06-27 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("play", "0023_game_tries2_alter_game_number2"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="pivot",
            field=models.IntegerField(null=True),
        ),
    ]
