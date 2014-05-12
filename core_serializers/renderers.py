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
            return 'text.html'
        if class_name == 'IntegerField':
            return 'text.html'
        if class_name == 'ChoiceField':
            if field.style.get('type') == 'radio':
                return 'radio.html'
            return 'select.html'
        return 'text.html'

    def render(self, data, **options):
        ret = ''
        for key, value, field in data.field_items():
            template_name = self.get_template_name(field)
            template = env.get_template(template_name)
            ret += template.render(value=value, field=field) + '\n'
        return ret
