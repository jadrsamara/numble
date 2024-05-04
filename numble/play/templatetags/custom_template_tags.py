from django import template

register = template.Library()


@register.simple_tag
def get_value_2d(l, i, j):
    try:
        return l[i][j]
    except:
        return None
    

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
def get_value_1d(l, i):
    try:
        return l[i]
    except:
        return None
    

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