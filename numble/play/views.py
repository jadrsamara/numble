from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout

import hashlib

base_template = "play/index.html"
base_reverse = "play:index"


def index(request):

    is_logged_in = False
    if request.user.is_authenticated:
        is_logged_in = True

    return render(
        request,
        base_template,
        {
            "is_logged_in": is_logged_in,
        }
    )


def signup_view(request):
    template_name = "play/signup.html"
    return render(
        request,
        template_name,
    )


@require_http_methods(["POST"])
def user(request):

    def validate(request):
        email = User.objects.filter(email=request.POST["email"])
        username = User.objects.filter(username=request.POST["username"])

        if len(list(email)) > 0:
            return render(
                request,
                "play/signup.html",
                {
                    "error_message": "Email is already registered!",
                },
            )
        
        if len(list(username)) > 0:
            return render(
                request,
                "play/signup.html",
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

    # user = authenticate(username=request.POST["username"], password=hashlib.sha256(request.POST["password"].encode('utf-8')).hexdigest())
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse(base_reverse))
    else:
        return render(
                request,
                "play/signup.html",
                {
                    "error_message": "Unexpected Error!",
                },
        )


def login_view(request):
    template_name = "play/login.html"
    return render(
        request,
        template_name,
    )


@require_http_methods(["POST"])
def login_user_view(request):
    
    username = request.POST["username"]
    password = hashlib.sha256(request.POST["password"].encode('utf-8')).hexdigest()

    user_username = authenticate(username=username, password=password)
    user_email = authenticate(email=username, password=password)

    if user_username is not None:
        login(request, user_username)
    elif user_email is not None:
        login(request, user_email)
    else:
        template_name = "play/login.html"
        return render(
            request,
            template_name,
            {
                "error_message": "Please enter the correct username and password"
            },
        )

    return HttpResponseRedirect(reverse(base_reverse))


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(reverse(base_reverse))


def play_view(request):

    template_name = "play/play.html"
    
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse(base_reverse))

    return render(
        request,
        template_name,
    )