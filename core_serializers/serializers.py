from collections import OrderedDict
from core_serializers import fields
from core_serializers.fields import *
import copy


class DeserializedObject(object):
    """
    A basic object that simply sets whatever attributes are
    passed to it at initialization.

    The default Serializer class uses this on `create()`.
    """

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value) 

    def __str__(self):
        attributes = str(self.__dict__).lstrip('{').rstrip('}')
        return '<Deserialized object %s>' % attributes


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


class Serializer(fields.Field):
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
            field.setup(field_name, self)

    def setup(self, field_name, serializer):
        # If the serializer is used as a field then it needs to provide
        # the current context to all it's child fields.
        super(Serializer, self).setup(field_name, serializer)
        for field_name, field in self.fields.items():
            field.setup(field_name, serializer)

    def validate(self, data):
        """
        Validate the given data and return a dictionary of validated values.
        """
        ret = {}
        for field_name, field in self.fields.items():
            input_value = data.get(field_name, empty)
            native_value = field.validate(input_value)
            if native_value is empty:
                continue
            field.set_item(ret, native_value)

        return ret

    def create(self, data):
        """
        Validate the given data and return an object instance.
        """
        data = self.validate(data)
        return DeserializedObject(**data)

    def update(self, instance, data):
        """
        Validate the given data and use it to update an existing object instance.
        """
        data = self.validate(data)
        for key, value in data.items():
            setattr(instance, key, value)

    def serialize(self, instance):
        """
        Given an object instance, return it as serialized data.
        """
        ret = {}
        for field_name, field in self.fields.items():
            native_value = field.get_attribute(instance)
            output_value = field.serialize(native_value)
            if output_value is empty:
                continue
            ret[field_name] = output_value

        return ret
