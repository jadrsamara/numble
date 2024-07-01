from django import template

from .. models import Game, Streak

register = template.Library()


@register.simple_tag
def get_value_2d(l, i, j):
    try:
        return l[i][j]
    except:
        return None
    

@register.simple_tag
def get_blind(game, i):
    try:
        correct = 0
        partial = 0
        for i, try_number in enumerate(game.tries[f"try{i+1}"]):
            if try_number == game.number[i]:
                correct += 1
            elif try_number in game.number:
                partial += 1
        return {
            "correct": correct,
            "partial": partial,
        }
    except:
        return {
            "correct": 0,
            "partial": 0,
        }
    

@register.simple_tag
def get_color(game, i, j):
    try:
        i += 1
        if game.tries[f"try{i}"][j] == game.number[j]:
            return 'green'
        elif game.tries[f"try{i}"][j] in game.number:
            return 'orange'
        return 'gray'
    except:
        return None
    

@register.simple_tag
def get_color_by_number(number, try_number, j):
    try:
        if number[j] == try_number[j]:
            return 'green'
        elif try_number[j] in number:
            return 'orange'
        return 'gray'
    except:
        return None
    

@register.simple_tag
def get_color_by_numbers(number, number2, try_number, j):
    try:
        if number[j] == try_number[j] or number2[j] == try_number[j]:
            return 'green'
        elif try_number[j] in number or try_number[j] in number2:
            return 'orange'
        return 'gray'
    except:
        return None
    
    
@register.simple_tag
def get_2d_color(game, i, j):
    try:
        i += 1
        if game.tries2[f"try{i}"][j] == game.number2[j]:
            return 'green'
        elif game.tries2[f"try{i}"][j] in game.number2:
            return 'orange'
        return 'gray'
    except:
        return None
    

@register.simple_tag
def get_value_1d(l, i):
    try:
        return l[i]
    except:
        return None
    
    
@register.simple_tag
def increment(i):
    return i+1
    

@register.simple_tag
def get_theme(request):
    try:
        return request.session['dark_mode']
    except:
        return 'light'
    

@register.simple_tag
def get_user_stats(user):
    streak = Streak.objects.filter(user=user).first()
    if streak == None:
        streak = 0
    else:
        streak = streak.streak

    number_of_daily_games = Game.objects.filter(user=user, game_mode='daily', game_completed=True).count()
    return {
        "dailies": number_of_daily_games,
        "streak": streak,
    }


@register.simple_tag
def get_user_streaks(games, game_mode):

    users_dict = dict()
    users_wl_raation_dict = dict()

    for game in games:
        users_dict.update({game.user.pk: 0})

    for user in users_dict:

        if game_mode == 'daily':
            dailies = Game.objects.filter(user=user, game_completed=True, game_mode='daily').count()
            users_dict[user] = dailies
        else:
            streak = Streak.objects.filter(user=user).first()
            if streak == None:
                streak = 0
            else:
                streak = streak.streak
            users_dict[user] = streak

        total_games = Game.objects.filter(user=user, game_completed=True).count()
        total_games_won = Game.objects.filter(user=user, game_completed=True, game_won=True).count()
        users_wl_raation_dict[user] = f'{(total_games_won/total_games)*100:.2f}'.rstrip('0').rstrip('.')
    
    return (users_dict, users_wl_raation_dict)


@register.simple_tag
def get_user_streak(user, user_streaks):
    return user_streaks[0][user.pk]


@register.simple_tag
def get_user_wl_ratio(user, user_streaks):
    return user_streaks[1][user.pk]


def pretty_time_delta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%dd %dh %dm %ds' % (days, hours, minutes, seconds)
    elif hours > 0:
        return '%dh %d m %ds' % (hours, minutes, seconds)
    elif minutes > 0:
        return '%dm %ds' % (minutes, seconds)
    else:
        return '%ds' % (seconds,)


@register.filter
def convert_to_readable_time(time):    
    return pretty_time_delta(time.total_seconds())