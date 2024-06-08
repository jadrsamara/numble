from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import F

import os
import random as random
import datetime
import random as random_with_seed
import re
import time
import requests
import json
import gzip
from io import BytesIO


from .models import Game, Leaderboard, Streak
# from .templatetags.custom_template_tags import convert_to_readable_time


base_template = "play/index.html"
base_reverse = "play:index"

GAME_TRIES_LIMIT = 7
game_modes = ['easy', 'medium', 'hard', 'daily', '1v1']



# --- Home ---


def index(request):
    return render(
        request,
        base_template,
    )


def health_check(request):
    return HttpResponse("success")


def about_view(request):
    return HttpResponse("made by Jad Samara\ncontact@numble.one")


def switch_theme_view(request):

    page = reverse(base_reverse)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        page = referer.replace(request.META.get('HTTP_ORIGIN'), '')

    if 'dark_mode' not in request.session:
        request.session['dark_mode'] = 'dark'
        return HttpResponseRedirect(page)
    
    if request.session['dark_mode'] == 'light':
        request.session['dark_mode'] = 'dark'
    else:
        request.session['dark_mode'] = 'light'
    return HttpResponseRedirect(page)


# --- User Views ---


def signup_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse(base_reverse))
    template_name = "play/regestration/signup.html"
    return render(
        request,
        template_name,
    )

 
def is_valid_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False
    

def is_valid_username(username):
    regex = r'\b[a-zA-Z0-9\.\_]*\b'
    if(re.fullmatch(regex, username)):
        return True
    else:
        return False


@require_http_methods(["POST"])
def signup_done_view(request):

    sign_up_template = 'play/regestration/signup.html'

    def validate(request):

        if len(request.POST["email"]) > 50 or len(request.POST["username"]) > 20:
            return render(
                request,
                sign_up_template,
                {
                    "error_message": "Email or Username exceeded the character limit",
                },
            )
        
        if not is_valid_email(request.POST["email"]):
            return render(
                request,
                sign_up_template,
                {
                    "error_message": "Email is invalid",
                },
            )
        
        if not is_valid_username(request.POST["username"]):
            return render(
                request,
                sign_up_template,
                {
                    "error_message": "Username is invalid, it should only contain: . or _",
                },
            )

        email = User.objects.filter(email=request.POST["email"])
        username = User.objects.filter(username=request.POST["username"])

        if len(list(email)) > 0:
            return render(
                request,
                sign_up_template,
                {
                    "error_message": "Email is already registered!",
                },
            )
        
        if len(list(username)) > 0:
            return render(
                request,
                sign_up_template,
                {
                    "error_message": "Username is already registered!",
                },
            )
        return True

    validation_result = validate(request)
    if validation_result != True:
        return validation_result

    user = User.objects.create_user(
        username=request.POST["username"],
        email=request.POST["email"],
        password=request.POST["password"],
        first_name=request.POST["firstname"],
        last_name=request.POST["lastname"],
    )

    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse(base_reverse))
    else:
        return render(
                request,
                sign_up_template,
                {
                    "error_message": "Unexpected Error!",
                },
        )


def login_view(request):
    next_page = request.GET.get('next') if request.GET.get('next') is not None else reverse(base_reverse)

    if request.user.is_authenticated:
        return HttpResponseRedirect(next_page)
    
    template_name = "play/regestration/login.html"
    return render(
        request,
        template_name,
    )


@require_http_methods(["POST"])
def login_done_view(request):
    next_page = request.GET.get('next') if request.GET.get('next') is not None else reverse(base_reverse)
    
    username = request.POST["username"]
    password = request.POST["password"]

    user_username = authenticate(username=username, password=password)
    user_email = authenticate(email=username, password=password)

    if user_username is not None:
        login(request, user_username)
    elif user_email is not None:
        login(request, user_email)
    else:
        template_name = "play/regestration/login.html"
        return render(
            request,
            template_name,
            {
                "error_message": "incorrect login credentials!",
            },
        )

    return HttpResponseRedirect(next_page)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(reverse(base_reverse))


# --- App Views ---


# @login_required(login_url='/login/')
def play_view(request):

    template_name = "play/play.html"

    return render(
        request,
        template_name,
    )


def generate_numbers_by_seed(seed, number_of_digits):
    random_with_seed.seed(seed)
    numbers = list(range(10))
    random_with_seed.shuffle(numbers)
    return numbers[:number_of_digits]


def get_a_new_game_number(game_mode):
    number_pool = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
    if game_mode == 'easy':
        game_number = random.sample(number_pool, 4)
        return ''.join(str(num) for num in game_number)
    if game_mode == 'medium':
        game_number = random.sample(number_pool, 5)
        return ''.join(str(num) for num in game_number)
    if game_mode == 'hard':
        game_number = random.sample(number_pool, 6)
        return ''.join(str(num) for num in game_number)
    if game_mode == 'daily':
        game_number = generate_numbers_by_seed(int(str((datetime.datetime.now(datetime.timezone.utc).date())).replace('-', '')), number_of_digits=4)
        return ''.join(str(num) for num in game_number)


def get_user_from_request(request) -> User:
    if request.user.is_anonymous:
        try:
            return User.objects.get(username='Anonymous')
        except User.DoesNotExist:
            return User.objects.create_user(
                username='Anonymous',
                email='anon@anon',
                password=os.environ['AnonUserPass'],
                first_name='',
                last_name='',
            )
    else:
        return request.user


# @login_required(login_url='/login/')
def game_view(request, game_mode):
    """
    Creates a new game if user has no current games
    Redirects to the new / unfinished game
    """

    if game_mode not in game_modes:
        return HttpResponseNotFound()
    
    user = get_user_from_request(request)

    if not request.user.is_anonymous:
        game = Game.objects.filter(user=user, game_completed=False, game_mode=game_mode).first()
    else: 
        game = None

    if game_mode == 'daily':
        game = Game.objects.filter(user=user, date=timezone.now().date(), game_mode=game_mode).first()

    if game == None:
        game = Game.objects.create_game(
            user = user,
            game_mode = game_mode, 
            number = get_a_new_game_number(game_mode),
        )

    game_id = game.pk

    if type(game.expire_time) == datetime.datetime:
        expire_time = game.expire_time.time()
    else:
        expire_time = game.expire_time

    expire_time = datetime.datetime.combine(date=game.expire_date, time=expire_time, tzinfo=datetime.timezone.utc)
    if expire_time < timezone.now():
        game.game_completed = True
        game.finish_time = timezone.now()
        game.duration = expire_time - datetime.datetime.combine(date=game.date, time=game.start_time, tzinfo=datetime.timezone.utc)
        game.game_won = False
    
        game.save()

        # return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))


    return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))


# @login_required(login_url='/login/')
def game_by_id_view(request, game_mode, game_id):

    game = Game.objects.filter(pk=game_id, game_mode=game_mode).first()
    
    if game == None:
        return HttpResponseNotFound()
        
    can_current_request_user_play = not game.game_completed and ((game.user == request.user) or ((game.user.username == 'Anonymous') and (request.user.is_anonymous)))
    
    expire_time = datetime.datetime.combine(date=game.expire_date, time=game.expire_time, tzinfo=datetime.timezone.utc)
    if not game.game_completed and (datetime.datetime.combine(date=game.expire_date, time=game.expire_time, tzinfo=datetime.timezone.utc) < timezone.now()):
        game.game_completed = True
        game.finish_time = timezone.now()
        game.duration = expire_time - datetime.datetime.combine(date=game.date, time=game.start_time, tzinfo=datetime.timezone.utc)
        game.game_won = False
        can_current_request_user_play = False
        game.save()
    
    tries = []
    for i in range(1, GAME_TRIES_LIMIT + 1):
        game_try = game.tries.get(f"try{i}")
        if game_try is None:
            break
        tries.append(game_try)

    template_name = "play/game.html"

    return render(
        request,
        template_name,
        {
            "game_tries": tries,
            "game_tries_range": range(len(tries)),
            "game_mode_range": range(len(get_a_new_game_number(game_mode))),
            "game_mode_len": len(get_a_new_game_number(game_mode)),
            "GAME_TRIES_LIMIT": GAME_TRIES_LIMIT,
            "can_current_request_user_play": can_current_request_user_play,
            "game": game,
        },
    )


def game_won_options(game: Game, user: User, game_mode: str):
    
    if user.username == 'Anonymous':
        return

    def user_game_streak():
        streak = Streak.objects.filter(user=user).first()

        if streak == None:
            streak = Streak.objects.create_streak(user=user)
            return

        if streak.date == timezone.now():
            streak.date = timezone.now() + timezone.timedelta(days=1)
            streak.streak = F("streak") + 1
            streak.save()
            return

        if streak.date - timezone.timedelta(days=1) == timezone.now():
            return
        
        streak.date = timezone.now() + timezone.timedelta(days=1)
        streak.streak = 1
        streak.save()
        return
    
    user_game_streak()

    top_games = Leaderboard.objects.filter(game_mode=game_mode)

    top_games = sorted(list(top_games), key=lambda x: x.rank, reverse=False)

    if len(top_games) == 0:
        Leaderboard.objects.create_leaderboard_item(game, user, game_mode, 1)
        return

    already_created = False

    for i, leaderboard_game in enumerate(top_games):

        if already_created and len(top_games) > 20 and i >= 20:
            leaderboard_game.delete()
            continue
        
        if already_created:
            leaderboard_game.rank = F("rank") + 1
            leaderboard_game.save()
            continue

        if game.number_of_tries < leaderboard_game.game.number_of_tries:
            Leaderboard.objects.create_leaderboard_item(game, user, game_mode, leaderboard_game.rank)
            leaderboard_game.rank = F("rank") + 1
            leaderboard_game.save()
            already_created = True
            continue

        if game.number_of_tries == leaderboard_game.game.number_of_tries and game.duration < leaderboard_game.game.duration:
            Leaderboard.objects.create_leaderboard_item(game, user, game_mode, leaderboard_game.rank)
            leaderboard_game.rank = F("rank") + 1
            leaderboard_game.save()
            already_created = True
            continue

        try:
            top_games[i+1]
            if game.number_of_tries < top_games[i+1].game.number_of_tries:
                Leaderboard.objects.create_leaderboard_item(game, user, game_mode, leaderboard_game.rank + 1)
                already_created = True
                continue

            if game.number_of_tries == top_games[i+1].game.number_of_tries and game.duration < top_games[i+1].game.duration:
                Leaderboard.objects.create_leaderboard_item(game, user, game_mode, leaderboard_game.rank + 1)
                already_created = True
                continue
        
        except IndexError:
            pass
    
    if len(top_games) < 20 and not already_created:
        Leaderboard.objects.create_leaderboard_item(game, user, game_mode, len(top_games) + 1)


@require_http_methods(["POST"])
def game_forfeit_view(request, game_mode, game_id):
    
    user = get_user_from_request(request)
    game = Game.objects.filter(pk=game_id, user=user, game_mode=game_mode).first()
    
    if game == None:
        return HttpResponseNotFound()
    
    if game.game_completed:
        return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))
    
    expire_time = datetime.datetime.combine(date=game.expire_date, time=game.expire_time, tzinfo=datetime.timezone.utc)
    game.game_completed = True
    game.finish_time = timezone.now()
    game.duration = expire_time - datetime.datetime.combine(date=game.date, time=game.expire_time, tzinfo=datetime.timezone.utc)
    game.game_won = False

    game.save()

    return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))
    

# @login_required(login_url='/login/')
@require_http_methods(["POST"])
def game_submit_view(request, game_mode, game_id):

    user = get_user_from_request(request)

    game = Game.objects.filter(pk=game_id, user=user, game_mode=game_mode).first()
    
    if game == None:
        return HttpResponseNotFound()
    
    if game.game_completed:
        return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))
    
    expire_time = datetime.datetime.combine(date=game.expire_date, time=game.expire_time, tzinfo=datetime.timezone.utc)
    if datetime.datetime.combine(date=game.expire_date, time=game.expire_time, tzinfo=datetime.timezone.utc) < timezone.now():
        game.game_completed = True
        game.finish_time = timezone.now()
        game.duration = expire_time - datetime.datetime.combine(date=game.date, time=game.expire_time, tzinfo=datetime.timezone.utc)
        game.game_won = False
    
        game.save()

        return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))

    new_number_try = []

    for i in range(len(get_a_new_game_number(game_mode))):
        cell = request.POST[f"input_cell{i}"]
        if not 2 > len(cell) > 0:
            return HttpResponseServerError()
        new_number_try.append(cell)
    
    new_number_try = ''.join(str(x) for x in new_number_try)

    number_of_tries = game.number_of_tries
    number_of_tries += 1
    game.number_of_tries = number_of_tries

    tries = game.tries

    tries[f"try{number_of_tries}"] = new_number_try
    game.tries = tries

    if number_of_tries >= GAME_TRIES_LIMIT or game.number == new_number_try:
        game.game_completed = True
        game.finish_time = timezone.now()

        start_time = datetime.datetime.combine(date=game.date, time=game.start_time, tzinfo=datetime.timezone.utc)

        game.duration = datetime.datetime.now(datetime.timezone.utc) - start_time

        if game.number == new_number_try:
            game.game_won = True
            game_won_options(game, user, game_mode)
    
    game.save()

    return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))


def user_profile(request, username):

    profile_user = User.objects.get(username=username)

    is_same_user = False
    if request.user == profile_user:
        is_same_user = True

    game_history = Game.objects.filter(user=profile_user, game_completed=True).order_by("-pk")[:5]

    template_name = "play/user_profile.html"

    profile_initials = (profile_user.first_name[0] if len(profile_user.first_name)>0 else '') + (profile_user.last_name[0] if len(profile_user.last_name)>0 else '')
    if profile_initials == '':
        profile_initials = profile_user.username[0]

    total_games = Game.objects.filter(user=profile_user, game_completed=True).count()
    games_won = Game.objects.filter(user=profile_user, game_completed=True, game_won=True).count()
    games_lost = total_games - games_won

    is_history_empty = len(game_history) == 0

    player_stats = {
        "games_played": total_games,
        "games_won": games_won,
        "games_lost": games_lost,
    }

    streak = Streak.objects.filter(user=profile_user).first()
    if streak == None:
        streak = 0
    else:
        streak = streak.streak

    number_of_daily_games = Game.objects.filter(user=profile_user, game_mode='daily', game_completed=True).count()

    return render(
        request,
        template_name,
        {
            "is_same_user": is_same_user,
            "profile_user": profile_user,
            "game_history": game_history,
            "profile_initials": profile_initials,
            "is_friend": 'Follow', # TODO
            "player_stats": player_stats,
            "is_history_empty": is_history_empty,
            "streak": streak,
            "daily_games": number_of_daily_games,
        },
    )

def leaderboard_view(request):

    template_name = "play/leaderboard.html"

    Leaderboard_game_modes = game_modes[:]
    Leaderboard_game_modes.remove('daily')
    Leaderboard_game_modes.remove('1v1')

    request_game_mode = request.GET.get('game_mode')
    if request_game_mode in Leaderboard_game_modes:
        top_games = Leaderboard.objects.filter(game_mode=request_game_mode)
    else:
        top_games = Leaderboard.objects.filter(game_mode='easy')
        request_game_mode = 'easy'

    top_games = sorted(list(top_games), key=lambda x: x.rank, reverse=False)

    Leaderboard_game_modes.remove(request_game_mode)

    is_list_empty = len(top_games) == 0
    
    return render(
            request,
            template_name,
            {
                "is_list_empty": is_list_empty,
                "top_games": top_games,
                "game_mode": request_game_mode,
                "other_modes": Leaderboard_game_modes,
            }
           )

def test_view(request):
    return 'hi'
