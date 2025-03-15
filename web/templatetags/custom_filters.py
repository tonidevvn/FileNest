from django import template

register = template.Library()


@register.filter
def endswith(value, arg):
    """
    Check if a string ends with the specified suffix.
    Usage: {{ filename|endswith:'.pdf' }}
    """
    return value.endswith(arg) if value else False
