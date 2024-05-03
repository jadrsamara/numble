from django import template

register = template.Library()


@register.simple_tag
def get_value(l, i, j):
    try:
        return l[i][j]
    except:
        return None