# Generated by Django 5.0.4 on 2024-10-24 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("play", "0028_alter_game_number2"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="number2",
            field=models.CharField(max_length=10, null=True),
        ),
    ]
