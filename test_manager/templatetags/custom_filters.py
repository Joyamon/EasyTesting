from django import template
from django.utils.safestring import mark_safe
import json
import pprint

register = template.Library()


@register.filter
def pprint(value):
    """
    Pretty print JSON or dict objects
    """
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except:
            pass

    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return value


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using the key
    """
    if not dictionary:
        return None

    if isinstance(dictionary, str):
        try:
            dictionary = json.loads(dictionary)
        except:
            return None

    return dictionary.get(key)


@register.filter
def percentage(value, total):
    """Calculate percentage of value from total"""
    if total == 0:
        return 0
    return (value / total) * 100


@register.filter
def multiply(value, arg):
    """将值乘以参数"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0