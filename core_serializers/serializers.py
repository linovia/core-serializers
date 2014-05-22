from collections import OrderedDict
from core_serializers.fields import (
    ValidationError, BaseField, Field, empty, is_html_input
)
from core_serializers.utils import (
    BasicObject, FieldDict, parse_html_dict, parse_html_list
)
import copy


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
                  if isinstance(obj, BaseField)]
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

    def __init__(self, partial=False, **kwargs):
        super(Serializer, self).__init__(**kwargs)
        self.partial = partial

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

    def get_primitive_value(self, dictionary):
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
            primitive_value = field.get_primitive_value(data)
            try:
                native_value = field.validate(primitive_value)
            except ValidationError as exc:
                errors[field.field_name] = str(exc)
            else:
                field.set_native_value(ret, native_value)

        if errors:
            raise ValidationError(errors)
        return ret

    def to_primitive(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = FieldDict(serializer=self)

        for field in self.fields.values():
            native_value = field.get_native_value(instance)
            primitive_value = field.serialize(native_value)
            field.set_primitive_value(ret, primitive_value)

        return ret

    def create(self, data):
        """
        Validate the given data and return an object instance.
        """
        data = self.validate(data)
        return BasicObject(**data)

    def update(self, instance, data):
        """
        Validate the given data and use it to update an existing object instance.
        """
        data = self.validate(data)
        for key, value in data.items():
            setattr(instance, key, value)


class ListSerializer(Field):
    def __init__(self, child_serializer, **kwargs):
        super(ListSerializer, self).__init__(**kwargs)
        self.child_serializer = child_serializer
        child_serializer.setup('', self, self)

    def setup(self, field_name, parent, root):
        # If the list is used as a field then it needs to provide
        # the current context to the child serializer.
        super(ListSerializer, self).setup(field_name, parent, root)
        self.child_serializer.setup(field_name, self, root)

    def get_primitive_value(self, dictionary):
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

    def to_primitive(self, data):
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
