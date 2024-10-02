from django.urls import path, re_path
from django.contrib.auth import views as auth_views

from . import views

app_name = "play"

urlpatterns = [

    # --- Home ---

    path("", views.index, name="index"),
    path("about/", views.about_view, name="about_view"),
    path("health/", views.health_view, name="health_view"),
    path("switch_theme/", views.switch_theme_view, name="switch_theme_view"),

    # path("test_view/", views.test_view, name="test_view"),

    # --- User paths ---

    # path("user/", views.user, name="user"), 
    re_path(r"^user/(?P<username>[a-zA-Z0-9\.\_]*)/$", views.user_profile, name="user_profile"),
    # re_path(r"^user/(?P<username>[a-zA-Z0-9\.\_]*)/edit/$", views.user_edit_profile, name="user_edit_profile"),
    # re_path(r"^user/(?P<username>[a-zA-Z0-9\.\_]*)/edit/done/$", views.user_edit_profile_done, name="user_edit_profile_done"),

    path("signup/", views.signup_view, name="signup_view"),
    path("signup/done/", views.signup_done_view, name="signup_done_view"),
    
    path("login/", views.login_view, name="login_view"),
    path("login/done/", views.login_done_view, name="login_done_view"),

    path("logout/", views.logout_view, name="logout_view"),

    # most likely no need since user can change password from edit profile
    # path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    # path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),

    # request a password change
    path('password_reset/', views.password_reset_view, name='password_reset_view'),
    # link from email (query parameters)
    path('password_reset/submit/', views.password_reset_submit_view, name='password_reset_submit_view'),
    path('password_reset/done/', views.password_reset_done_view, name='password_reset_done_view'),

    # --- App ---

    path("play/", views.play_view, name="play_view"),

    path("games/<slug:game_mode>/", views.game_view, name="game_view"),
    path("games/<slug:game_mode>/<int:game_id>/", views.game_by_id_view, name="game_by_id_view"),
    path("games/<slug:game_mode>/<int:game_id>/submit/", views.game_submit_view, name="game_submit_view"),
    path("games/<slug:game_mode>/<int:game_id>/forfeit/", views.game_forfeit_view, name="game_forfeit_view"),

    path("leaderboard/", views.leaderboard_view, name="leaderboard_view"),
]

