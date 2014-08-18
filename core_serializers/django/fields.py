import sys

from core_serializers.utils import empty
from core_serializers import fields


class DjangoField(object):
    def __init__(self, read_only=False, write_only=False,
                 required=None, default=empty, initial=None, source=None,
                 label=None, style=None, *args, **kwargs):
        return super(DjangoField, self).__init__(read_only, write_only,
                 required, default, initial, source,
                 label, style)

class Field(DjangoField, fields.Field):
    pass

# Generate the alter ego from core_serializers.fields which would inherit
# the DjangoField Mixin
module = sys.modules[__name__]
for cls_name in ('IntegerField', 'CharField', 'BooleanField'):
    setattr(module, cls_name, type(cls_name, (DjangoField, getattr(fields, cls_name)), {}))
