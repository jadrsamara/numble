from django.urls import path, include

from . import views

app_name = "play"

urlpatterns = [
    path("", views.index, name="index"),
    path("user", views.user, name="user"),
    path("signup", views.signup_view, name="signup_view"),
    path("login", views.login_view, name="login_view"),
    path("login_user", views.login_user_view, name="login_user_view"),
    path("logout", views.logout_view, name="logout_view"),
    path("play", views.play_view, name="play_view"),
    # path("user/<slug:slug>", views.userprofile, name="userprofile"),
    # path('accounts', include('django.contrib.auth.urls')),
    # path("login-user", views.login_user, name="login-user"),
    # path("user", views.user, name="userprofile"),
    # path("leaderboard", views.LeaderboardListView.as_view(), name="leaderboard"),
]
