from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('core_serializers', 'templates'))


class FormRenderer(object):
    def get_template_name(self, field):
        class_name = field.__class__.__name__
        if getattr(field, 'read_only', False):
            return 'readonly.html'
        if class_name == 'BooleanField':
            return 'checkbox.html'
        if class_name == 'CharField':
            if field.style.get('type') == 'textarea':
                return 'textarea.html'
            return 'input.html'
        if class_name == 'IntegerField':
            return 'input.html'
        if class_name == 'ChoiceField':
            if field.style.get('type') == 'radio':
                return 'select_radio.html'
            return 'select.html'
        if class_name == 'MultipleChoiceField':
            if field.style.get('type') == 'checkbox':
                return 'select_checkbox.html'
            return 'select_multiple.html'
        return 'input.html'

    def render(self, data, **options):
        ret = ''
        for key, value, field in data.field_items():
            template_name = self.get_template_name(field)
            template = env.get_template(template_name)
            ret += template.render(value=value, field=field) + '\n'
        return ret
