from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required



import hashlib

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


@login_required(login_url='/login/')
def game_view(request):
    """
    Creates a new game if user has no current games
    Redirects to the new / unfinished game
    """
    game_id = 15

    return HttpResponseRedirect(f'/game/{game_id}')


@login_required(login_url='/login/')
def game_by_id_view(request, game_id):
    print(game_id)
    raise NotImplementedError