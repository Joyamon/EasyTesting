from django import template
from django.utils.safestring import mark_safe
import json
import pprint

register = template.Library()


@register.filter
def pprint(value):
    """Pretty print a JSON or dict object"""
    if isinstance(value, str):
        try:
            # Try to parse as JSON
            parsed = json.loads(value)
            return json.dumps(parsed, indent=2, sort_keys=True)
        except (ValueError, TypeError):
            # If not JSON, return as is
            return value
    elif isinstance(value, (dict, list)):
        # If already a dict or list, pretty print it
        return json.dumps(value, indent=2, sort_keys=True)
    else:
        # For other types, use Python's pprint
        return pprint.pformat(value)


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def percentage(value, total):
    """Calculate percentage of value from total"""
    if total == 0:
        return 0
    return (value / total) * 100
