class empty:
    pass


def get_attribute(instance, key):
    """
    Similar to 'getattr', but additionally allows:

    'nested.lookup' - getattr(getattr(obj, 'nested'), 'lookup')
    '*'             - return object without lookup
    """
    if key == '*':
        return instance
    elif '.' in key:
        left, right = key.split('.', 1)
        return get_attribute(getattr(instance, left), right)
    return getattr(instance, key)


def set_item(dictionary, key, value):
    """
    Similar to `__setitem__`, but additionally allows:

    'nested.lookup' - dictionary['nested']['lookup'] = value
    '*'             - dictionary.update(value)
    """
    if key == '*':
        dictionary.update(value)
    elif '.' in key:
        left, right = key.split('.', 1)
        dictionary = dictionary.get(left, {})
        set_item(dictionary[left], right, value)
    else:
        dictionary[key] = value


class Field(object):
    _creation_counter = 0

    def __init__(self, read_only=False, write_only=False,
            required=None, default=None, source=None, context=None):

        # The creation counter is required so that the serializer metaclass
        # can determine the ordering of the fields on the class.
        self._creation_counter = Field._creation_counter
        Field._creation_counter += 1

        # If `required` is unset, then use `True` unless a default is provided.
        if required is None:
            required = default is None and not read_only

        # Some combinations of keyword arguments do not make sense.
        assert not (read_only and write_only), 'May not set both `read_only` and `write_only`'
        assert not (read_only and required), 'May not set both `read_only` and `required`'
        assert not (read_only and default), 'May not set both `read_only` and `default`'
        assert not (required and default), 'May not set both `required` and `default`'

        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.default = default
        self.source = source
        self.context = {} if context is None else context
        # label, help_text, validators, widget

    def setup(self, field_name, serializer, partial):
        self.serializer = serializer
        if self.source is None:
            self.source = field_name
        if partial:
            self.required = False

    def _set_context(self, context):
        self.context = context

    def _set_partial(self):
        self.required = False

    def _get_default(self):
        if self.required:
            raise ValueError('required')
        return self.default

    def set_item(self, dictionary, value):
        set_item(dictionary, key=self.source, value=value)

    def get_attribute(self, instance):
        return get_attribute(instance, key=self.source)

    def validate(self, data):
        """
        Validate a simple representation and return the internal value.

        The provided data may be `empty` if no representation was included.
        May return `empty` if the field should not be included in the validated data.
        """
        if self.read_only:
            return empty
        if data is empty:
            return self._get_default()
        return data

    def serialize(self, value):
        """
        Serialize an internal value and return the simple representation.

        May return `empty` if the field should not be serialized.
        """
        if self.write_only:
            return empty
        return value


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
