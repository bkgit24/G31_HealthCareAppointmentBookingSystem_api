from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def length_is(value, arg):
    """Check if the length of the value equals the argument"""
    try:
        return len(value) == int(arg)
    except (ValueError, TypeError):
        return False 