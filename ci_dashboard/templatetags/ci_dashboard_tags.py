from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """Get a value from a dictionary by key."""
    if isinstance(d, dict):
        return d.get(key)
    return None


@register.filter
def get_item(dictionary, key):
    """Alternative filter for getting dict items."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def mul(value, arg):
    """Multiply value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""


@register.filter
def div(value, arg):
    """Divide value by arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return ""
