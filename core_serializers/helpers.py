from jinja2 import Markup
from core_serializers.renderers import FormRenderer


def render_form(data, **options):
    renderer = FormRenderer()
    return Markup(renderer.render(data, **options))


def render_field(field_item, **options):
    renderer = FormRenderer()
    return Markup(renderer.render_field(field_item, **options))
