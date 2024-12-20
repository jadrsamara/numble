from typing import Any
from django.conf import settings
from django.db import models
from django.utils import timezone
from secrets import token_urlsafe
import newrelic.agent


class GameManager(models.Manager):

    @newrelic.agent.function_trace()
    def create_game(self, user, game_mode, number, expire_duration):
        game = self.create(
            user = user,
            game_mode = game_mode,
            number = number,
            date = timezone.now().date(),
            start_time = timezone.now(),
            expire_time = timezone.now() + timezone.timedelta(minutes=expire_duration),
            expire_date = (timezone.now() + timezone.timedelta(minutes=expire_duration)).date(),
        )
        return game
    
    @newrelic.agent.function_trace()
    def create_2d_game(self, user, game_mode, number, number2, pivot, expire_duration):
        game = self.create(
            user = user,
            game_mode = game_mode,
            number = number,
            number2 = number2,
            pivot = pivot,
            date = timezone.now().date(),
            start_time = timezone.now(),
            expire_time = timezone.now() + timezone.timedelta(minutes=expire_duration),
            expire_date = (timezone.now() + timezone.timedelta(minutes=expire_duration)).date(),
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
    expire_time = models.TimeField()
    expire_date = models.DateField()
    number_of_tries = models.IntegerField(default=0)
    game_mode = models.CharField( 
        max_length = 6,
        choices = 
        {
            "easy": "Easy Game Mode",
            "medium": "Medium Game Mode",
            "hard": "Hard Game Mode",
            "daily": "Daily Numble",
            "blind": "Blind Game Mode",
            "2d": "2 Dimensional Game Mode"
        },
    )
    game_completed = models.BooleanField(default=False)
    number = models.CharField(max_length=10)
    number2 = models.CharField(max_length=10, null=True)
    pivot = models.IntegerField(null=True)
    tries = models.JSONField(default=dict)
    tries2 = models.JSONField(default=dict, null=True)
    game_won = models.BooleanField(default=False)
    lose_reason = models.CharField(blank=True, null=True, max_length=256)

    objects = GameManager()

    @newrelic.agent.function_trace()
    def save(self, *args, **kwargs):
        # Trace the save method (INSERT/UPDATE in the DB)
        super().save(*args, **kwargs)

    @newrelic.agent.function_trace()
    def delete(self, *args, **kwargs):
        # Trace the delete method (DELETE in the DB)
        super().delete(*args, **kwargs)


class LeaderboardManager(models.Manager):

    @newrelic.agent.function_trace()
    def create_leaderboard_item(self, game, user, game_mode, rank):
        leaderboard_item = self.create(
            user = user,
            game_mode = game_mode,
            rank = rank,
            date = timezone.now().date(),
            game = game
        )
        return leaderboard_item


class Leaderboard(models.Model):
    rank = models.IntegerField()
    game_mode = game_mode = models.CharField( 
        max_length = 6,
        choices = 
        {
            "easy": "Easy Game Mode",
            "medium": "Medium Game Mode",
            "hard": "Hard Game Mode",
            "daily": "Daily Numble",
            "ubest": "User's Best Game"
        },
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
    )
    date = models.DateField()

    objects = LeaderboardManager()

    @newrelic.agent.function_trace()
    def save(self, *args, **kwargs):
        # Trace the save method (INSERT/UPDATE in the DB)
        super().save(*args, **kwargs)

    @newrelic.agent.function_trace()
    def delete(self, *args, **kwargs):
        # Trace the delete method (DELETE in the DB)
        super().delete(*args, **kwargs)


class StreakManager(models.Manager):

    @newrelic.agent.function_trace()
    def create_streak(self, user):
        streak = self.create(
            user = user,
            streak = 1,
            date = (timezone.now() + timezone.timedelta(days=1)).date(),
        )
        return streak


class Streak(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    date = models.DateField()
    streak = models.IntegerField(default=0)

    objects = StreakManager()

    @newrelic.agent.function_trace()
    def save(self, *args, **kwargs):
        # Trace the save method (INSERT/UPDATE in the DB)
        super().save(*args, **kwargs)

    @newrelic.agent.function_trace()
    def delete(self, *args, **kwargs):
        # Trace the delete method (DELETE in the DB)
        super().delete(*args, **kwargs)


class ResetPasswordManager(models.Manager):

    @newrelic.agent.function_trace()
    def create_reset_password(self, user):
        reset_password = self.create(
            user = user,
            date_reset_counter = 0,
            date = timezone.now(),
            expire_date = timezone.now() + timezone.timedelta(minutes=15),
            token = f'{token_urlsafe()}{token_urlsafe()}'
        )
        return reset_password


class ResetPassword(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField()
    expire_date = models.DateTimeField()
    date_reset_counter = models.IntegerField(default=0)
    token = models.CharField(max_length=100)

    objects = ResetPasswordManager()

    @newrelic.agent.function_trace()
    def save(self, *args, **kwargs):
        # Trace the save method (INSERT/UPDATE in the DB)
        super().save(*args, **kwargs)

    @newrelic.agent.function_trace()
    def delete(self, *args, **kwargs):
        # Trace the delete method (DELETE in the DB)
        super().delete(*args, **kwargs)