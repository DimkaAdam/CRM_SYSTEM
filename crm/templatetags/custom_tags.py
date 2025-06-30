from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def dictkey(value, key):
    return value.get(key) if isinstance(value, dict) else None