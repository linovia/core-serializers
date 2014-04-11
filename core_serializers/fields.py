class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


class IgnoreField(Exception):
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

    def set_value(self, dictionary, value):
        dictionary[self.field_name] = value

    def get_value(self, instance):
        return getattr(instance, self.field_name)

    def validate(self, data):
        return data

    def serialize(self, value):
        return value


class Field(BaseField):
    def __init__(self, read_only=False, write_only=False,
                 required=None, default=empty, source=None):
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

    def setup(self, field_name, parent, root):
        """
        Setup the context for the field instance.
        """
        self.field_name = field_name
        self.parent = parent
        self.root = root
        if self.source is None:
            self.source = field_name
        if root.partial:
            self.required = False

    def set_value(self, dictionary, value):
        """
        Given a dictionary, set the key that this field should populate
        after validation.
        """
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

    def get_value(self, instance):
        """
        Given an object instance, return the attribute value that this
        field should serialize.
        """
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

    def get_default(self):
        """
        Return the default value to use when validating data if no input
        is provided for this field.

        If a default has not been set for this field then this will simply
        return `empty`, indicating that no value should be set in the
        validated data for this field.
        """
        return self.default

    def validate(self, data):
        """
        Validate a simple representation and return the internal value.

        The provided data may be `empty` if no representation was included.
        May return `empty` if the field should not be included in the validated data.
        """
        if self.read_only:
            return empty
        elif data is empty and self.required:
            raise ValueError('required')
        elif data is empty:
            return self.get_default()
        return data

    def serialize(self, value):
        """
        Serialize an internal value and return the simple representation.

        May return `empty` if the field should not be serialized.
        """
        if self.write_only:
            return empty
        return value


### Typed field classes

class BooleanField(Field):
    def validate(self, data):
        data = super(BooleanField, self).validate(data)
        if data in ('true', 't', 'True', '1'):
            return True
        if data in ('false', 'f', 'False', '0'):
            return False
        return bool(data)


class CharField(Field):
    def validate(self, data):
        data = super(CharField, self).validate(data)
        return str(data)


class IntegerField(Field):
    def validate(self, data):
        data = super(IntegerField, self).validate(data)
        try:
            data = int(str(data))
        except (ValueError, TypeError):
            raise ValueError('invalid integer')
        return data


### Complex field classes

class SerializerMethodField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(SerializerMethodField, self).__init__(**kwargs)

    def serialize(self, value):
        attr = 'get_%s' % self.field_name
        method = getattr(self.parent, attr)
        return method(value)
