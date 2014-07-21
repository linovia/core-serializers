from six import add_metaclass
from collections import OrderedDict, namedtuple
from core_serializers.fields import (
    SkipField, ValidationError, Field
)
from core_serializers.utils import (
    BasicObject, parse_html_dict, parse_html_list, empty, is_html_input, set_value
)
import copy


FieldResult = namedtuple('FieldResult', ['field', 'value', 'error'])


class BaseSerializer(Field):
    def __init__(self, instance=None, data=None, **kwargs):
        super(BaseSerializer, self).__init__(**kwargs)
        self.instance = instance
        self._initial_data = data

    def to_native(self, data):
        raise NotImplementedError()

    def to_primative(self, instance):
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    def is_valid(self):
        try:
            self._validated_data = self.to_native(self._initial_data)
        except ValidationError as exc:
            self._validated_data = {}
            self._errors = exc.args[0]
            return False
        self._errors = {}
        return True

    @property
    def data(self):
        if not hasattr(self, '_data'):
            if self.instance is not None:
                self._data = self.to_primative(self.instance)
            elif self._initial_data is not None:
                self._data = {
                    field_name: field.get_value(self._initial_data)
                    for field_name, field in self.fields.items()
                }
            else:
                self._data = self.get_initial()
        return self._data

    @property
    def errors(self):
        if not hasattr(self, '_errors'):
            msg = 'You must call `.is_valid()` before accessing `.errors`.'
            raise AssertionError(msg)
        return self._errors

    @property
    def validated_data(self):
        if not hasattr(self, '_validated_data'):
            msg = 'You must call `.is_valid()` before accessing `.validated_data`.'
            raise AssertionError(msg)
        return self._validated_data


class SerializerMetaclass(type):
    """
    This metaclass sets a dictionary named `_fields` on the class.

    Any fields included as attributes on either the class or it's superclasses
    will be include in the `_fields` dictionary.
    """

    @classmethod
    def _get_fields(cls, bases, attrs):
        fields = [(field_name, attrs.pop(field_name))
                  for field_name, obj in list(attrs.items())
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


@add_metaclass(SerializerMetaclass)
class Serializer(BaseSerializer):

    def __init__(self, *args, **kwargs):
        super(Serializer, self).__init__(*args, **kwargs)

        # Every new serializer is created with a clone of the field instances.
        # This allows users to dynamically modify the fields on a serializer
        # instance without affecting every other serializer class.
        self.fields = copy.deepcopy(self._fields)

        # Setup all the child fields, to provide them with the current context.
        for field_name, field in self.fields.items():
            field.bind(field_name, self, self)

    def bind(self, field_name, parent, root):
        # If the serializer is used as a field then when it becomes bound
        # it also needs to bind all its child fields.
        super(Serializer, self).bind(field_name, parent, root)
        for field_name, field in self.fields.items():
            field.bind(field_name, self, root)

    def get_initial(self):
        return {
            field.field_name: field.get_initial()
            for field in self.fields.values()
        }

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
        fields = [field for field in self.fields.values() if not field.read_only]

        for field in fields:
            primitive_value = field.get_value(data)
            try:
                validated_value = field.validate(primitive_value)
            except ValidationError as exc:
                errors[field.field_name] = str(exc)
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise ValidationError(errors)

        return ret

    def to_primative(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = [field for field in self.fields.values() if not field.write_only]

        for field in fields:
            native_value = field.get_attribute(instance)
            ret[field.field_name] = field.to_primative(native_value)

        return ret

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)

    def create(self, validated_data):
        return BasicObject(**validated_data)

    def save(self):
        if self.instance is not None:
            self.update(self.instance, self.validated_data)
        self.instance = self.create(self.validated_data)
        return self.instance

    def __iter__(self):
        errors = self.errors if hasattr(self, '_errors') else {}
        for field in self.fields.values():
            value = self.data.get(field.field_name) if self.data else None
            error = errors.get(field.field_name)
            yield FieldResult(field, value, error)


class ListSerializer(BaseSerializer):
    child = None
    initial = []

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert self.child is not None, '`child` is a required argument.'
        super(ListSerializer, self).__init__(*args, **kwargs)
        self.child.bind('', self, self)

    def bind(self, field_name, parent, root):
        # If the list is used as a field then it needs to provide
        # the current context to the child serializer.
        super(ListSerializer, self).bind(field_name, parent, root)
        self.child.bind(field_name, self, root)

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

        return [self.child.validate(item) for item in data]

    def to_primative(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [self.child.to_primative(item) for item in data]

    def create(self, attrs_list):
        return [BasicObject(**attrs) for attrs in attrs_list]

    def save(self):
        if self.instance is not None:
            self.update(self.instance, self.validated_data)
        self.instance = self.create(self.validated_data)
        return self.instance
