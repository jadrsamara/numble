from typing import Any
from django.conf import settings
from django.db import models
from django.utils import timezone


class GameManager(models.Manager):
    def create_game(self, user, game_mode, number):
        game = self.create(
            user = user,
            game_mode = game_mode,
            number = number,
            date = timezone.now().date(),
            start_time = timezone.now(),
        )
        return game


class Game(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    date = models.DateField()
    start_time = models.TimeField()
    finish_time = models.TimeField(null=True)
    duration = models.DurationField(null=True)
    number_of_tries = models.IntegerField(default=0)
    game_mode = models.CharField( 
        max_length = 6,
        choices = 
        {
            "easy": "Easy Game Mode",
            "medium": "Medium Game Mode",
            "hard": "Hard Game Mode",
            "daily": "Daily Numble",
        },
    )
    game_completed = models.BooleanField(default=False)
    number = models.CharField(max_length=10)
    tries = models.JSONField(default=dict)
    game_won = models.BooleanField(default=False)

    objects = GameManager()
