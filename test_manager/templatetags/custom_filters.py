from django import template
import json

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
