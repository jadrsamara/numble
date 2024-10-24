from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError, HttpResponseForbidden, HttpResponseBadRequest
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db.models import F

import os
import random as random
import datetime
import random as random_with_seed
import logging
import re
import requests
import json
import newrelic.agent

from secrets import token_urlsafe

from .models import Game, Leaderboard, Streak, ResetPassword


base_template = "play/index.html"
base_reverse = "play:index"

GAME_TRIES_LIMIT = {
    'easy': 7, 
    'medium': 7, 
    'hard': 7, 
    'daily': 7, 
    'blind': 12, 
    '1v1': 7,
    '2d': 7,
}
GAME_TIMEOUT = 15
game_modes = ['easy', 'medium', 'hard', 'daily', 'blind', '2d']


request_logger = logging.getLogger("django")


# --- Home ---

@newrelic.agent.function_trace()
def index(request):
    return render(
        request,
        base_template,
    )


@newrelic.agent.function_trace()
def about_view(request):
    return HttpResponse("made by Jad Samara\ncontact@numble.one\n")


@newrelic.agent.function_trace()
def health_view(request):
    return HttpResponse("success")


@newrelic.agent.function_trace()
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


@newrelic.agent.function_trace()
def signup_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse(base_reverse))
    template_name = "play/regestration/signup.html"
    return render(
        request,
        template_name,
    )

 
@newrelic.agent.function_trace()
def is_valid_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False
    

@newrelic.agent.function_trace()
def is_valid_username(username):

    if not len(username) >= 3:
        return False

    regex = r'\b[a-zA-Z0-9\.\_]*\b'
    if(re.fullmatch(regex, username)):
        return True
    else:
        return False


@require_http_methods(["POST"])
@newrelic.agent.function_trace()
def signup_done_view(request):

    sign_up_template = 'play/regestration/signup.html'

    @newrelic.agent.function_trace()
    def validate(request):

        if len(request.POST["email"]) > 50 or len(request.POST["username"]) > 20:
            return render(
                request,
                sign_up_template,
                {
                    "error_message": "Email or Username exceeded the character limit",
                },
            )
        
        if len(request.POST["password"]) < 8:
            return render(
                request,
                sign_up_template,
                {
                    "error_message": "Password is less than 8 characters long",
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

    logger_message = 'New user created'
    request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})

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


@newrelic.agent.function_trace()
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
@newrelic.agent.function_trace()
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

    logger_message = 'New user login'
    request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})
    return HttpResponseRedirect(next_page)


@newrelic.agent.function_trace()
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(reverse(base_reverse))


# --- App Views ---


# @login_required(login_url='/login/')
@newrelic.agent.function_trace()
def play_view(request):

    template_name = "play/play.html"

    return render(
        request,
        template_name,
    )


@newrelic.agent.function_trace()
def generate_numbers_by_seed(seed, number_of_digits):
    random_with_seed.seed(seed)
    numbers = list(range(10))
    random_with_seed.shuffle(numbers)
    return numbers[:number_of_digits]


@newrelic.agent.function_trace()
def get_a_new_game_number(game_mode, request):
    number_pool = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
    if game_mode in ['easy', 'blind', '2d']:
        game_number = random.sample(number_pool, 4)
        return ''.join(str(num) for num in game_number)
    if game_mode == 'medium':
        game_number = random.sample(number_pool, 5)
        return ''.join(str(num) for num in game_number)
    if game_mode == 'hard':
        game_number = random.sample(number_pool, 6)
        return ''.join(str(num) for num in game_number)
    if game_mode == 'daily' and request.user.is_anonymous:
        game_number = generate_numbers_by_seed(int(str((datetime.datetime.now(datetime.timezone.utc).date())).replace('-', '')), number_of_digits=4)
        return ''.join(str(num) for num in game_number)
    if game_mode == 'daily' and not request.user.is_anonymous:
        game_number = random.sample(number_pool, 4)
        return ''.join(str(num) for num in game_number)
    

@newrelic.agent.function_trace()
def get_2d_game_number2(number):
    number_pool = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
    pivot_point_values = list(range(4))
    pivot_point = random.sample(pivot_point_values, 1)[0]
    print(number)
    print(pivot_point)
    pivoted_num = int(number[pivot_point])
    number_pool.remove(pivoted_num)
    number2 = random.sample(number_pool, 3)
    number2.insert(pivot_point, pivoted_num)
    return ''.join(str(num) for num in number2) , pivot_point


@newrelic.agent.function_trace()
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
@newrelic.agent.function_trace()
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

    if game_mode == 'daily' and not request.user.is_anonymous:
        game = Game.objects.filter(user=user, date=timezone.now().date(), game_mode=game_mode).first()

    if game_mode == '2d' and game == None:

        number1 = get_a_new_game_number(game_mode, request)
        print(number1)
        number2, pivot = get_2d_game_number2(number1)

        if game_mode == '2d':
            game = Game.objects.create_2d_game(
            user = user,
            game_mode = game_mode, 
            number = number1,
            number2 = number2,
            pivot = pivot,
            expire_duration = GAME_TIMEOUT,
        )
                
    if game == None:
        game = Game.objects.create_game(
            user = user,
            game_mode = game_mode, 
            number = get_a_new_game_number(game_mode, request),
            expire_duration = GAME_TIMEOUT,
        )

    game_id = game.pk

    if type(game.expire_time) == datetime.datetime:
        expire_time = game.expire_time.time()
    else:
        expire_time = game.expire_time

    expire_time = datetime.datetime.combine(date=game.expire_date, time=expire_time, tzinfo=datetime.timezone.utc)
    if expire_time < timezone.now() and not game.game_completed:
        game.game_completed = True
        game.finish_time = timezone.now()
        game.duration = expire_time - datetime.datetime.combine(date=game.date, time=game.start_time, tzinfo=datetime.timezone.utc)
        game.lose_reason = 'Timed out'
        game.game_won = False
    
        game.save()

        logger_message = f'{game.game_mode} game lost'
        request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})

        # return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))


    return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))


# @login_required(login_url='/login/')
@newrelic.agent.function_trace()
def game_by_id_view(request, game_mode, game_id):

    game = Game.objects.filter(pk=game_id, game_mode=game_mode).first()
    
    if game == None:
        return HttpResponseNotFound()
        
    can_current_request_user_play = not game.game_completed and ((game.user == request.user) or ((game.user.username == 'Anonymous') and (request.user.is_anonymous)))
    
    expire_time = datetime.datetime.combine(date=game.expire_date, time=game.expire_time, tzinfo=datetime.timezone.utc)
    if not game.game_completed and (expire_time < timezone.now()):
        game.game_completed = True
        game.finish_time = timezone.now()
        game.duration = expire_time - datetime.datetime.combine(date=game.date, time=game.start_time, tzinfo=datetime.timezone.utc)
        game.game_won = False
        game.lose_reason = 'Timed out'
        can_current_request_user_play = False
        game.save()

        logger_message = f'{game.game_mode} game lost'
        request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})
    
    tries = []
    last_try = None
    for i in range(1, GAME_TRIES_LIMIT[game_mode] + 1):
        game_try = game.tries.get(f"try{i}")
        if game_try is None:
            break
        tries.append(game_try)
        last_try = game_try

    tries2 = []
    last_try2 = None
    if game.tries2 is not None:
        for i in range(1, GAME_TRIES_LIMIT[game_mode] + 1):
            game_try2 = game.tries2.get(f"try{i}")
            if game_try2 is None:
                break
            tries2.append(game_try2)
            last_try2 = game_try2

    if game_mode == 'blind':
        template_name = "play/game_blind.html"
    elif game_mode == '2d':
        template_name = "play/game_2d.html"
    else:
        template_name = "play/game.html"

    return render(
        request,
        template_name,
        {
            "game_tries": tries,
            "game_tries2": tries2,
            "game_tries_range": range(len(tries)),
            "game_last_try": last_try,
            "game_last_try2": last_try2,
            "game_mode_range": range(len(get_a_new_game_number(game_mode, request))),
            "game_mode_len": len(get_a_new_game_number(game_mode, request)),
            "GAME_TRIES_LIMIT": GAME_TRIES_LIMIT[game_mode],
            "can_current_request_user_play": can_current_request_user_play,
            "game": game,
        },
    )


@newrelic.agent.function_trace()
def game_won_options(game: Game, user: User, game_mode: str, request):
    
    if user.username == 'Anonymous':
        return

    @newrelic.agent.function_trace()
    def user_game_streak():
        streak = Streak.objects.filter(user=user).first()

        if streak == None:
            streak = Streak.objects.create_streak(user=user)
            logger_message = 'player has no streak '+str({
                "user": str(user),
                "streak": streak.streak,
                "streak.date": str(streak.date),
                "current date": str(timezone.now().date())
            })
            request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})
            return

        if streak.date == timezone.now().date():
            logger_message = 'player has extended their streak '+str({
                "user": str(user),
                "streak": streak.streak,
                "streak.date": str(streak.date),
                "current date": str(timezone.now().date())
            })
            request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})
            streak.date = timezone.now().date() + timezone.timedelta(days=1)
            streak.streak = F("streak") + 1
            streak.save()
            return

        if streak.date - timezone.timedelta(days=1) >= timezone.now().date():
            logger_message = 'no action, player already has a streak for today '+str({
                "user": str(user),
                "streak": streak.streak,
                "streak.date": str(streak.date),
                "current date": str(timezone.now().date())
            })
            request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})
            return
        
        logger_message = 'reset streak to 1 '+str({
            "user": str(user),
            "streak": streak.streak,
            "streak.date": str(streak.date),
            "current date": str(timezone.now())
        })
        request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})
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
@newrelic.agent.function_trace()
def game_forfeit_view(request, game_mode, game_id):
    
    user = get_user_from_request(request)
    game = Game.objects.filter(pk=game_id, user=user, game_mode=game_mode).first()
    
    if game == None:
        return HttpResponseNotFound()
    
    if game.game_completed:
        # return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))
        return htmx_game_submit(request, game)

    expire_time = datetime.datetime.combine(date=game.expire_date, time=game.expire_time, tzinfo=datetime.timezone.utc)
    game.game_completed = True
    game.finish_time = timezone.now()
    game.duration = expire_time - datetime.datetime.combine(date=game.date, time=game.expire_time, tzinfo=datetime.timezone.utc)
    game.lose_reason = 'Game forfeited'
    game.game_won = False

    game.save()

    logger_message = f'{game.game_mode} game lost'
    request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})

    # return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))
    return htmx_game_submit(request, game)


@newrelic.agent.function_trace()
def htmx_game_submit(request, game):

    tries = []
    last_try = '0000'
    for i in range(1, GAME_TRIES_LIMIT[game.game_mode] + 1):
        game_try = game.tries.get(f"try{i}")
        if game_try is None:
            break
        tries.append(game_try)
        last_try = game_try

    tries2 = []
    last_try2 = None
    if game.tries2 is not None:
        for i in range(1, GAME_TRIES_LIMIT[game.game_mode] + 1):
            game_try2 = game.tries2.get(f"try{i}")
            if game_try2 is None:
                break
            tries2.append(game_try2)
            last_try2 = game_try2


    if game.game_mode == 'blind':
        template_name = 'play/htmx-blind-game-submit.html'
    elif game.game_mode == '2d':
        template_name = 'play/htmx-game-2d-submit.html'
    else:
        template_name = 'play/htmx-game-submit.html'

    return render(
        request,
        template_name,
        {
            "game_tries": tries,
            "game_tries2": tries2,
            "game_tries_range": range(len(game.tries)),
            "game_mode_range": range(len(game.number)),
            "game": game,
            "game_last_try": last_try,
            "game_last_try2": last_try2,
        }
    )


@require_http_methods(["POST"])
@newrelic.agent.function_trace()
def game_submit_view(request, game_mode, game_id):

    user = get_user_from_request(request)

    game = Game.objects.filter(pk=game_id, user=user, game_mode=game_mode).first()
    
    if game == None:
        return HttpResponseNotFound()
    
    if game.game_completed:
        # return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))
        return htmx_game_submit(request, game)
    
    expire_time = datetime.datetime.combine(date=game.expire_date, time=game.expire_time, tzinfo=datetime.timezone.utc)
    if expire_time < timezone.now():
        game.game_completed = True
        game.finish_time = timezone.now()
        game.duration = expire_time - datetime.datetime.combine(date=game.date, time=game.expire_time, tzinfo=datetime.timezone.utc)
        game.lose_reason = 'Timed out'
        game.game_won = False
    
        game.save()

        logger_message = f'{game_mode} game lost'
        request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})

        # return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))
        return htmx_game_submit(request, game)

    new_number_try = []

    for i in range(len(get_a_new_game_number(game_mode, request))):
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

    if_2d_check_won = True
    if game_mode == '2d':
        new_number2_try = []
        for i in range(len(get_a_new_game_number(game_mode, request))):
            try:
                cell = request.POST[f"input_cell2_{i}"]
            except KeyError:
                cell = request.POST[f"input_cell{i}"]
            if not 2 > len(cell) > 0:
                return HttpResponseServerError()
            new_number2_try.append(cell)
        
        new_number2_try = ''.join(str(x) for x in new_number2_try)

        tries2 = game.tries2

        tries2[f"try{number_of_tries}"] = new_number2_try
        game.tries2 = tries2

        if not (game.number == new_number_try and game.number2 == new_number2_try):
            if_2d_check_won = False


    if number_of_tries >= GAME_TRIES_LIMIT[game_mode] or (game.number == new_number_try and if_2d_check_won):
        game.game_completed = True
        game.finish_time = timezone.now()

        start_time = datetime.datetime.combine(date=game.date, time=game.start_time, tzinfo=datetime.timezone.utc)

        game.duration = datetime.datetime.now(datetime.timezone.utc) - start_time

        if game.number == new_number_try:
            game.game_won = True
            game_won_options(game, user, game_mode, request)
            logger_message = f'{game.game_mode} game won'
            request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})
        else:
            game.lose_reason = 'No more tries left'
            logger_message = f'{game.game_mode} game lost'
            request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})
    
    game.save()

    # return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))
    return htmx_game_submit(request, game)


@newrelic.agent.function_trace()
def user_profile(request, username):

    profile_user = get_object_or_404(User, username=username)

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

@newrelic.agent.function_trace()
def leaderboard_view(request):

    template_name = "play/leaderboard.html"

    Leaderboard_game_modes = game_modes[:]
    try:
        Leaderboard_game_modes.remove('1v1')
    except ValueError:
        pass

    request_game_mode = request.GET.get('game_mode')

    @newrelic.agent.function_trace()
    def return_top_games(request_game_mode):
        if request_game_mode in Leaderboard_game_modes:
            top_games = Leaderboard.objects.filter(game_mode=request_game_mode)
        else:
            top_games = Leaderboard.objects.filter(game_mode='easy')
            request_game_mode = 'easy'
        return top_games, request_game_mode
    
    top_games, request_game_mode = return_top_games(request_game_mode)

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


@newrelic.agent.function_trace()
def password_reset_view(request):

    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse(base_reverse))
    
    template_name = 'play/password-reset/password-reset.html'

    try:
        email_or_username = request.POST["email_or_username"]
    except KeyError:
        email_or_username = False

    if not email_or_username:
        return render(
            request,
            template_name,
        )
    
    error = send_reset_password_email_if_eligible(request)

    if error:
        return render(
            request,
            template_name,
            {
                "email_or_username": email_or_username,
                "error_message": error,
            }
        )

    return render(
        request,
        template_name,
        {
            "email_or_username": email_or_username,
            "disabled": "disabled",
            "disabled_color": "gray",
        }
    )


@newrelic.agent.function_trace()
def send_reset_password_email_if_eligible(request):

    if not 50 >= len(request.POST["email_or_username"]) >= 3:
        return 'The entered Email / Username is invalid'
    
    if not is_valid_email(request.POST["email_or_username"]) and not is_valid_username(request.POST["email_or_username"]):
        return 'The entered Email / Username is invalid'

    email = User.objects.filter(email=request.POST["email_or_username"])
    username = User.objects.filter(username=request.POST["email_or_username"])

    user = False

    if len(list(email)) > 0:
        user = list(email)[0]

    if len(list(username)) > 0:
        user = list(username)[0]
    
    if user:
        success = generate_new_token_and_send_reset_email(user, request)
        if not success:
            return "Error: something went wrong, please try again later"

    return False


@newrelic.agent.function_trace()
def generate_new_token_and_send_reset_email(user, request):

    reset_password = ResetPassword.objects.filter(user=user).first()

    if reset_password == None:
        reset_password = ResetPassword.objects.create_reset_password(user)

    user_date_counter = reset_password.date_reset_counter
    is_same_date = reset_password.date.date() == timezone.now().date()
    
    if is_same_date and user_date_counter >= 3:
        return False

    reset_password.date = timezone.now()
    reset_password.expire_date = timezone.now() + timezone.timedelta(minutes=15)
    reset_password.token = f'{token_urlsafe()}{token_urlsafe()}'

    if is_same_date:
        reset_password.date_reset_counter = user_date_counter + 1
    else:
        reset_password.date_reset_counter = 1
    
    reset_password.save()
    
    return send_reset_password_email(user.email, user.username, reset_password.token, request)


@newrelic.agent.function_trace()
def send_reset_password_email(email, username, token, request):
    api_key = os.environ['MJ_APIKEY_PUBLIC']
    api_secret = os.environ['MJ_APIKEY_PRIVATE']

    domain = os.environ['DOMAIN']

    # Email details
    sender_email = f'no-reply@{domain}'
    sender_name = 'Numble'

    recipient_email = email
    recipient_name = username

    # Mailjet template ID
    template_id = int(os.environ['MJ_TEMPLATE_ID'])

    # Variables to pass to the template
    variables = {
        'url': f'https://{domain}{reverse("play:password_reset_submit_view")}?token={token}',
        'username': username
    }

    # API endpoint for sending email
    url = 'https://api.mailjet.com/v3.1/send'

    # Email payload
    payload = {
        'Messages': [
            {
                'From': {
                    'Email': sender_email,
                    'Name': sender_name
                },
                'To': [
                    {
                        'Email': recipient_email,
                        'Name': recipient_name
                    }
                ],
                'TemplateID': template_id,
                'TemplateLanguage': True,
                'Variables': variables
            }
        ]
    }

    # Send the request
    response = requests.post(
        url,
        auth=(api_key, api_secret),
        headers={'Content-Type': 'application/json'},
        data=json.dumps(payload)
    )

    # log response
    if response.status_code == 200:
        logger_message = f'password reset email requested, {response.status_code} '+str({
            "user": str(username),
            "email": email,
            "response": response.json(),
            "payload": json.dumps(payload)
        })
        request_logger.info(logger_message, extra={'request': request, "logger_message": logger_message})
        return True
    else:
        logger_message = f'password reset email requested, {response.status_code} '+str({
            "user": str(username),
            "email": email,
            "response": response.json(),
            "payload": json.dumps(payload)
        })
        request_logger.warn(logger_message, extra={'request': request, "logger_message": logger_message})
        return False
    

@newrelic.agent.function_trace()
def password_reset_submit_view(request):

    token = request.GET.get("token", False)

    if token:
        valid_token = ResetPassword.objects.filter(token=token).first()
    else: 
        return HttpResponseForbidden()
    
    if valid_token == None:
        return HttpResponseForbidden()
    
    if valid_token.expire_date < timezone.now():
        return HttpResponseForbidden()
    
    template_name = 'play/password-reset/password-reset-submitted.html'

    return render(
        request,
        template_name,
        {
            "username": valid_token.user.username,
            "token": token,
        }
    )


@require_http_methods(["POST"])
@newrelic.agent.function_trace()
def password_reset_done_view(request):

    token = request.GET.get("token", False)
    password = request.POST.get("password", False)
    password2 = request.POST.get("password2", False)

    if not token:  
        return HttpResponseForbidden()
    
    if not password:
        return HttpResponseBadRequest()
    
    if token:
        valid_token = ResetPassword.objects.filter(token=token).first()
    else: 
        return HttpResponseForbidden()
    
    if valid_token.expire_date < timezone.now():
        return HttpResponseForbidden()
    
    template_name = 'play/password-reset/password-reset-submitted.html'

    error = False

    if len(password) < 8:
        error = True
        error_message = "Password is less than 8 characters long"
        
    if password != password2:
        error = True
        error_message = "The 2 entered passwords don't match"

    if error:
        return render(
            request,
            template_name,
            {
                "username": valid_token.user.username,
                "token": token,
                "error_message": error_message,
            }
        )
    else:
        valid_token.user.set_password(password)
        valid_token.user.save()

        login(request, valid_token.user)
        return HttpResponseRedirect(reverse(base_reverse))
