import markdown
from django import template
from django.utils.safestring import mark_safe
from urllib.parse import urlencode
from web.helpers import default_query_params

register = template.Library()

@register.filter(name='colour')
def colour(value):
    levels = {
        1: "warning",
        2: "primary",
        3: "primary",
        4: "secondary",
        5: "secondary",
    }
    return levels.get(value, "dark")

@register.filter(name='markdown')
def markdown_filter(text):
    md = markdown.Markdown()
    return mark_safe(md.convert(text))

@register.simple_tag(name='qs')
def qs(request, **overrides):
    """
    A tag that generates a query string based on the current request.

    It assumes that the template that uses this, is from a view that has 
    the `process_query_params` decorator applied to it. Because that 
    decorator will format all these query params the right way.
    """
    def convert(v):
        if v in [True, False]:
            return "yes" if v else "no"
        return v

    qs = {}
    for k in default_query_params.keys():
        v = request.GET.get(k)
        if v is not None:
            qs[k] = convert(v)

    for k, v in overrides.items():
        if not v and k in qs:
            del qs[k]
        elif v:
            qs[k] = convert(v)

    # Since this is the default, no point in passing it around.
    for k, v in default_query_params.items():
        if v is not None:
            if qs[k] == v:
                del qs[k] 

    return "?" + urlencode(qs) if qs else ""