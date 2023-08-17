from django import template
import base64
register = template.Library()

@register.filter
def base64_encode(value):
    # Your base64 encoding logic here
    encoded_value = base64.b64encode(value.encode('utf-8')).decode('utf-8')
    return encoded_value
