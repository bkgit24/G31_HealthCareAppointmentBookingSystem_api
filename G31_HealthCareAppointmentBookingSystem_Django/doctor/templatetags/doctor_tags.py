from django import template

register = template.Library()

@register.filter
def filter_unseen(notifications):
    return [n for n in notifications if not n.seen] 