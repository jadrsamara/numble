# Generated by Django 5.0.4 on 2024-10-24 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("play", "0026_alter_game_lose_reason"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="number2",
            field=models.CharField(default=0, max_length=10, null=True),
        ),
    ]