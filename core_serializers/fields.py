from core_serializers.utils import FieldDict


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


class ValidationError(Exception):
    pass


class BaseField(object):
    """
    This class is provided as the miminal field interface.

    It does not include any of the configuration options made available
    by the `Field` class, but may be overridden to provide for custom
    field behavior.
    """
    _creation_counter = 0

    def __init__(self):
        # The creation counter is required so that the serializer metaclass
        # can determine the ordering of the fields on the class.
        self._creation_counter = Field._creation_counter
        BaseField._creation_counter += 1

    def setup(self, field_name, parent, root):
        self.field_name = field_name
        self.parent = parent
        self.root = root

    def get_primitive_value(self, dictionary):
        return dictionary.get(self.field_name)

    def set_native_value(self, dictionary, value):
        dictionary[self.field_name] = value

    def get_native_value(self, instance):
        return getattr(instance, self.field_name)

    def set_primitive_value(self, dictionary, value):
        dictionary[self.field_name] = value

    def validate(self, data):
        return data

    def serialize(self, value):
        return value


class Field(BaseField):
    error_messages = {
        'required': 'This field is required.'
    }

    def __init__(self, read_only=False, write_only=False,
                 required=None, default=empty, initial=None, source=None):
        super(Field, self).__init__()

        # If `required` is unset, then use `True` unless a default is provided.
        if required is None:
            required = default is empty and not read_only

        # Some combinations of keyword arguments do not make sense.
        assert not (read_only and write_only), 'May not set both `read_only` and `write_only`'
        assert not (read_only and required), 'May not set both `read_only` and `required`'
        assert not (read_only and default is not empty), 'May not set both `read_only` and `default`'
        assert not (required and default is not empty), 'May not set both `required` and `default`'

        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.default = default
        self.source = source
        self.initial = initial

    def setup(self, field_name, parent, root):
        """
        Setup the context for the field instance.
        """
        self.field_name = field_name
        self.parent = parent
        self.root = root
        if self.source is None:
            self.source = field_name
        if getattr(root, 'partial', False):
            self.required = False

    def get_primitive_value(self, dictionary):
        return dictionary.get(self.field_name, empty)

    def set_native_value(self, dictionary, value):
        """
        Given a dictionary, set the key that this field should populate
        after validation.
        """
        if value is empty:
            return

        if self.source == '*':
            # Deal with special case '*' and update whole dictionary,
            # not just a single key in the dictionary.
            dictionary.update(value)
            return

        # Deal with regular or nested lookups.
        key = self.source
        while '.' in key:
            next, key = key.split('.', 1)
            dictionary = dictionary.get(next, {})

        dictionary[key] = value

    def get_native_value(self, instance=empty):
        """
        Given an object instance, return the attribute value that this
        field should serialize.
        """
        if instance is empty:
            return self.get_initial()

        if self.source == '*':
            # Deal with special case '*' and return the whole instance,
            # not just an attribute on the instance.
            return instance

        # Deal with regular or nested lookups.
        key = self.source
        while '.' in key:
            next, key = key.split('.', 1)
            instance = getattr(instance, next)

        return getattr(instance, key)

    def set_primitive_value(self, dictionary, value=empty):
        if value is empty:
            return
        if isinstance(dictionary, FieldDict):
            dictionary.set_item(self.field_name, value, field=self)
        else:
            dictionary[self.field_name] = value

    def get_default(self):
        """
        Return the default value to use when validating data if no input
        is provided for this field.

        If a default has not been set for this field then this will simply
        return `empty`, indicating that no value should be set in the
        validated data for this field.
        """
        return self.default

    def get_initial(self):
        return self.initial

    def validate(self, data=empty):
        """
        Validate a simple representation and return the internal value.

        The provided data may be `empty` if no representation was included.
        May return `empty` if the field should not be included in the
        validated data.
        """
        if self.read_only:
            return empty
        elif data is empty and self.required:
            raise ValidationError(self.error_messages['required'])
        elif data is empty:
            return self.get_default()
        return self.to_native(data)

    def serialize(self, value=empty):
        """
        Serialize an internal value and return the simple representation.

        May return `empty` if the field should not be serialized.
        """
        if self.write_only:
            return empty
        return self.to_primitive(value)

    def to_native(self, data):
        """
        native value <- primitive datatype.
        """
        return data

    def to_primitive(self, value):
        """
        native value -> primitive datatype.
        """
        return value


### Typed field classes


class BooleanField(Field):
    def to_native(self, data):
        if data in ('true', 't', 'True', '1'):
            return True
        if data in ('false', 'f', 'False', '0'):
            return False
        return bool(data)


class CharField(Field):
    def to_native(self, data):
        return str(data)


class IntegerField(Field):
    error_messages = {
        'required': 'This field is required.',
        'invalid_integer': 'A valid integer is required.'
    }

    def to_native(self, data):
        try:
            data = int(str(data))
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages['invalid_integer'])
        return data


### Complex field classes

class MethodField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(MethodField, self).__init__(**kwargs)

    def serialize(self, value):
        attr = 'get_%s' % self.field_name
        method = getattr(self.parent, attr)
        return method(value)
