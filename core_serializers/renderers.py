from jinja2 import Environment, PackageLoader
import json

env = Environment(loader=PackageLoader('core_serializers', 'templates'))


class FormRenderer:
    def render_field(self, value, field):
        class_name = field.__class__.__name__

        context = {}
        if getattr(field, 'read_only', False):
            base = 'readonly.html'
        elif class_name == 'BooleanField':
            base = 'checkbox.html'
        elif class_name == 'IntegerField':
            base = 'input.html'
            context = {'input_type': 'number'}
        elif class_name == 'ChoiceField':
            if field.style.get('type') == 'radio':
                base = 'select_radio.html'
            else:
                base = 'select.html'
        elif class_name == 'MultipleChoiceField':
            if field.style.get('type') == 'checkbox':
                base = 'select_checkbox.html'
            else:
                base = 'select_multiple.html'
        else:
            # CharField, and anything unknown
            if field.style.get('type') == 'textarea':
                base = 'textarea.html'
            else:
                base = 'input.html'
                context = {'input_type': 'text'}

        template_name = 'fields/vertical/' + base
        template = env.get_template(template_name)
        return template.render(value=value, field=field, **context)

    def render(self, data, **options):
        ret = ''
        for key, value, field in data.field_items():
            ret += self.render_field(value, field)
        return ret


class JSONRenderer:
    indent = None

    def __init__(self, indent=None):
        self.indent = self.indent if (indent is None) else indent

    def render(self, data, **options):
        indent = options.get('indent', self.indent)
        return json.dumps(data, indent=indent)
