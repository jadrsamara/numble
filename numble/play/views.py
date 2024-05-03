from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

import hashlib
import random

from .models import Game


base_template = "play/index.html"
base_reverse = "play:index"




# --- Home ---


def index(request):
    return render(
        request,
        base_template,
    )


# --- User Views ---


def signup_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse(base_reverse))
    template_name = "play/regestration/signup.html"
    return render(
        request,
        template_name,
    )


@require_http_methods(["POST"])
def signup_done_view(request):

    sign_up_template = 'play/regestration/signup.html'

    def validate(request):
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
        password=hashlib.sha256(request.POST["password"].encode('utf-8')).hexdigest(),
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
    password = hashlib.sha256(request.POST["password"].encode('utf-8')).hexdigest()

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
        )

    return HttpResponseRedirect(next_page)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(reverse(base_reverse))


# --- App Views ---


@login_required(login_url='/login/')
def play_view(request):

    template_name = "play/play.html"

    return render(
        request,
        template_name,
    )


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
    if game_mode == 'easy':
        raise NotImplementedError()
    

def update_game(game, number_of_tries, tries):
    game.number_of_tries = number_of_tries,
    game.tries = tries,
    game.save()


def complete_game(game, number_of_tries, tries):
    now = timezone.now()
    game.number_of_tries = number_of_tries,
    game.tries = tries,
    game.finish_time = now,
    game.duration = now - game.start_time,
    game.game_completed = True,
    game.save()


@login_required(login_url='/login/')
def game_view(request, game_mode):
    """
    Creates a new game if user has no current games
    Redirects to the new / unfinished game
    """

    if game_mode not in ['easy', 'medium', 'hard', 'daily']:
        return HttpResponseNotFound()

    game = Game.objects.filter(user=request.user, game_completed=False, game_mode=game_mode).first()
    if game == None:
        game = Game.objects.create_game(
            user = request.user,
            game_mode = game_mode, 
            number = get_a_new_game_number(game_mode)
        )

    game_id = game.pk

    return HttpResponseRedirect(f'/game/{game_mode}/{game_id}')


@login_required(login_url='/login/')
def game_by_id_view(request, game_mode, game_id):

    game = Game.objects.filter(pk=game_id, user=request.user, game_mode=game_mode).first()
    
    if game == None:
        return HttpResponseNotFound()
    
    tries = []
    for i in range(1, 10):
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
            "game_mode": game_mode,
            "game_id": game_id,
        },
    )


@login_required(login_url='/login/')
@require_http_methods(["POST"])
def game_submit_view(request, game_mode, game_id):

    game = Game.objects.filter(pk=game_id, user=request.user, game_mode=game_mode).first()
    
    if game == None:
        return HttpResponseNotFound()
    
    number_of_tries = game.number_of_tries
    if number_of_tries >= 10:
        raise NotImplementedError() 

    new_number_try = []

    for i in range(len(get_a_new_game_number(game_mode))):
        cell = request.POST[f"input_cell{i}"]
        if not 2 > len(cell) > 0:
            return HttpResponseServerError()
        new_number_try.append(cell)
    
    new_number_try = ''.join(str(x) for x in new_number_try)

    number_of_tries += 1
    game.number_of_tries = number_of_tries

    tries = game.tries

    tries[f"try{number_of_tries}"] = new_number_try
    game.tries = tries

    if number_of_tries == 10:
        # end game
        raise NotImplementedError()
    
    game.save()

    return HttpResponseRedirect(reverse("play:game_by_id_view", kwargs={"game_mode":game_mode, "game_id":game_id}))