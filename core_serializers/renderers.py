from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('core_serializers', 'templates'))


class FormRenderer(object):
    def render(self, data, **options):
        ret = ''
        for key, value, field in data.field_items():
            if getattr(field, 'read_only', False):
                template_file = 'readonly.html'
            else:
                template_file = {
                    'BooleanField': 'checkbox.html',
                    'CharField': 'text.html',
                    'IntegerField': 'text.html',
                }[field.__class__.__name__]
            template = env.get_template(template_file)
            ret += template.render(value=value, field=field) + '\n'
        print ret
        return ret