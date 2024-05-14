from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

import random as random
import datetime
import random as random_with_seed
import re

from .models import Game
from .templatetags.custom_template_tags import convert_to_readable_time


base_template = "play/index.html"
base_reverse = "play:index"

GAME_TRIES_LIMIT = 7




# --- Home ---


def index(request):
    return render(
        request,
        base_template,
    )


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
    regex = r'\b[a-zA-Z\.\_]*\b'
    if(re.fullmatch(regex, username)):
        return True
    else:
        return False


@require_http_methods(["POST"])
def signup_done_view(request):

    sign_up_template = 'play/regestration/signup.html'

    def validate(request):

        if len(request.POST["email"]) > 20 or len(request.POST["username"]) > 20:
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
        game_number = generate_numbers_by_seed(int(str((datetime.datetime.now().date())).replace('-', '')), number_of_digits=4)
        return ''.join(str(num) for num in game_number)


def get_user_from_request(request) -> User:
    if request.user.is_anonymous:
        return User.objects.get(username='Anonymous')
    else:
        return request.user


# @login_required(login_url='/login/')
def game_view(request, game_mode):
    """
    Creates a new game if user has no current games
    Redirects to the new / unfinished game
    """

    if game_mode not in ['easy', 'medium', 'hard', 'daily', '1v1']:
        return HttpResponseNotFound()
    
    user = get_user_from_request(request)

    if not request.user.is_anonymous:
        game = Game.objects.filter(user=user, game_completed=False, game_mode=game_mode).first()
    else: 
        game = None

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
    print(is_history_empty)

    player_stats = {
        "games_played": total_games,
        "games_won": games_won,
        "games_lost": games_lost,
    }

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
        },
    )

def leaderboard_view(request):
    """
    TODO: create a tabel for top 20 games + a tabel for top user game (his best game for each mode)
          these tabels should be updated when the game is complete and won

          leaderboard view should only read and display this table
          profile view should read the top user game table and add them as stats

          implement a today's leaderboard
    """
    top_20_games = []
    anonymous_user = User.objects.get(username='Anonymous')
    for i in range(1, 8):

        if len(top_20_games) >= 20:
            break
        
        today_date = datetime.datetime.now(datetime.timezone.utc).date()

        games = Game.objects.filter(~Q(user=anonymous_user), date=today_date, game_completed=True, number_of_tries=i)
        top_20_games += list(games)

        if len(games) >= 20:
            break

    print(len(top_20_games))
    for game in top_20_games:
        print(game.user)
        print(game.number_of_tries)
        print(convert_to_readable_time(game.duration))

    is_list_empty = len(top_20_games) == 0
    
    return render(
            request,
            base_template,
           )