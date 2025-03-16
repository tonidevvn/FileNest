from django import template

register = template.Library()

@register.filter
def get_item(obj, key):
    if isinstance(obj, dict):
        return obj.get(key)
    elif isinstance(obj, list):
        try:
            return obj[key]
        except IndexError:
            return None
    return None
