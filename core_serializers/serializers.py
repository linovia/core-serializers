from collections import OrderedDict, namedtuple
from core_serializers.fields import (
    ValidationError, Field, empty, is_html_input
)
from core_serializers.utils import (
    BasicObject, parse_html_dict, parse_html_list
)
import copy


FieldResult = namedtuple('FieldResult', ['field', 'value', 'error'])


class SerializerMetaclass(type):
    """
    This metaclass sets a dictionary named `_fields` on the class.

    Any fields included as attributes on either the class or it's superclasses
    will be include in the `_fields` dictionary.
    """

    @classmethod
    def _get_fields(cls, bases, attrs):
        fields = [(field_name, attrs.pop(field_name))
                  for field_name, obj in attrs.items()
                  if isinstance(obj, Field)]
        fields.sort(key=lambda x: x[1]._creation_counter)

        # If this class is subclassing another Serializer, add that Serializer's
        # fields.  Note that we loop over the bases in *reverse*. This is necessary
        # in order to maintain the correct order of fields.
        for base in bases[::-1]:
            if hasattr(base, '_fields'):
                fields = list(base._fields.items()) + fields

        return OrderedDict(fields)

    def __new__(cls, name, bases, attrs):
        attrs['_fields'] = cls._get_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)


class Serializer(Field):
    __metaclass__ = SerializerMetaclass

    def __init__(self, instance=None, data=None, partial=False, **kwargs):
        super(Serializer, self).__init__(**kwargs)
        self.instance = instance
        self.initial_data = data
        self.partial = partial

        self.validated_data, self.errors = (None, None)

        # Every new serializer is created with a clone of the field instances.
        # This allows users to dynamically modify the fields on a serializer
        # instance without affecting every other serializer class.
        self.fields = copy.deepcopy(self._fields)

        # Setup all the child fields, to provide them with the current context.
        for field_name, field in self.fields.items():
            field.setup(field_name, self, self)

    def setup(self, field_name, parent, root):
        # If the serializer is used as a field then it needs to provide
        # the current context to all it's child fields.
        super(Serializer, self).setup(field_name, parent, root)
        for field_name, field in self.fields.items():
            field.setup(field_name, self, root)

    def get_initial(self):
        return empty

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # nested HTML forms.
        if is_html_input(dictionary):
            return parse_html_dict(dictionary, prefix=self.field_name)
        return dictionary.get(self.field_name, empty)

    def to_native(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        ret = {}
        errors = {}

        for field in self.fields.values():
            value = field.get_value(data)
            try:
                validated_value = field.validate(value)
            except ValidationError as exc:
                errors[field.field_name] = str(exc)
            else:
                field.set_native_value(ret, validated_value)

        if errors:
            raise ValidationError(errors)

        return ret

    def serialize(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()

        for field in self.fields.values():
            native_value = field.get_native_value(instance)
            if field.write_only:
                continue
            ret[field.field_name] = field.serialize(native_value)

        return ret

    def is_valid(self):
        try:
            self.validated_data = self.validate(self.initial_data)
        except ValidationError, exc:
            self.validated_data = None
            self.errors = exc.message
            return False
        self.errors = None
        return True

    def save(self):
        if self.instance is not None:
            self.update(self.instance, self.validated_data)
        self.instance = self.create(self.validated_data)
        return self.instance

    def update(self, instance, attrs):
        for key, value in attrs.items():
            setattr(instance, key, value)

    def create(self, attrs):
        return BasicObject(**attrs)

    @property
    def data(self):
        if not hasattr(self, '_data'):
            if self.instance is not None:
                self._data = self.serialize(self.instance)
            elif self.initial_data is not None:
                self._data = {
                    field_name: field.get_value(self.initial_data)
                    for field_name, field in self.fields.items()
                }
            else:
                self._data = self.serialize(empty)
        return self._data

    def __iter__(self):
        for field in self.fields.values():
            value = self.data.get(field.field_name) if self.data else None
            error = self.errors.get(field.field_name) if self.errors else None
            yield FieldResult(field, value, error)


class ListSerializer(Field):
    def __init__(self, child, **kwargs):
        super(ListSerializer, self).__init__(**kwargs)
        self.child = child
        child.setup('', self, self)

    def setup(self, field_name, parent, root):
        # If the list is used as a field then it needs to provide
        # the current context to the child serializer.
        super(ListSerializer, self).setup(field_name, parent, root)
        self.child.setup(field_name, self, root)

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # lists in HTML forms.
        if is_html_input(dictionary):
            return parse_html_list(dictionary, prefix=self.field_name)
        return dictionary.get(self.field_name, empty)

    def to_native(self, data):
        """
        List of dicts of native values <- List of dicts of primitive datatypes.
        """
        if is_html_input(data):
            data = parse_html_list(data)

        # TODO: Skip empty returned results?
        ret = []

        for item in data:
            native_value = self.child_serializer.validate(item)
            ret.append(native_value)

        return ret

    def serialize(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        # TODO: Skip empty returned results?
        ret = []

        for item in data:
            primitive_value = self.child_serializer.serialize(item)
            ret.append(primitive_value)

        return ret

    def create(self, data):
        ret = []

        for item in data:
            native_value = self.child_serializer.create(item)
            ret.append(native_value)

        return ret

#     def update(self, instance, data):
#         TODO
