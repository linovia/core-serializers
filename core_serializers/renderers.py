from jinja2 import Environment, PackageLoader
import json

env = Environment(loader=PackageLoader('core_serializers', 'templates'))


class FormRenderer:
    template_name = 'form.html'

    def render_field(self, field_result, **options):
        field, value, error = field_result
        class_name = field.__class__.__name__
        layout = options.get('layout', 'vertical')

        context = {}
        if class_name == 'BooleanField':
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
            if field.style.get('type') == 'textarea' and layout != 'inline':
                base = 'textarea.html'
            else:
                base = 'input.html'
                context = {'input_type': 'text'}

        template_name = 'fields/' + layout + '/' + base
        template = env.get_template(template_name)
        return template.render(field=field, value=value, **context)

    def render(self, form, **options):
        style = getattr(getattr(form, 'Meta', None), 'style', {})
        layout = style.get('layout', 'vertical')
        template = env.get_template(self.template_name)
        return template.render(form=form, renderer=self, layout=layout)


class JSONRenderer:
    indent = None

    def __init__(self, indent=None):
        self.indent = self.indent if (indent is None) else indent

    def render(self, data, **options):
        indent = options.get('indent', self.indent)
        return json.dumps(data, indent=indent)
