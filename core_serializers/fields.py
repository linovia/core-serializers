class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


class ValidationError(Exception):
    pass


def is_html_input(dictionary):
    # MultiDict type datastructures are used to represent HTML form input,
    # which may have more than one value for each key.
    return hasattr(dictionary, 'getlist')


class BaseField(object):
    """
    This class is provided as a miminal field interface.

    It does not include any of the configuration options made available
    by the `Field` class, but may be overridden to provide for custom
    field behavior.
    """
    _creation_counter = 0

    _UNBOUND_FIELD = (
        'Cannot access attribute `{attr}` on field `{class_name}`. '
        'The field has not yet been bound to a serializer.'
    )

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

    # We protect `field_name`, `parent` and `root` attributes with accessors
    # that ensure the user gets a helpful traceback if attempting to call
    # methods on an unbound field.

    def get_field_name(self):
        try:
            return self._field_name
        except AttributeError:
            class_name = self.__class__.__name__
            msg = self._UNBOUND_FIELD.format(class_name=class_name, attr='field_name')
            raise AssertionError(msg)

    def get_parent(self):
        try:
            return self._parent
        except AttributeError:
            class_name = self.__class__.__name__
            msg = self._UNBOUND_FIELD.format(class_name=class_name, attr='parent')
            raise AssertionError(msg)

    def get_root(self):
        try:
            return self._root
        except AttributeError:
            class_name = self.__class__.__name__
            msg = self._UNBOUND_FIELD.format(class_name=class_name, attr='root')
            raise AssertionError(msg)

    def set_field_name(self, value):
        self._field_name = value

    def set_parent(self, value):
        self._parent = value

    def set_root(self, value):
        self._root = value

    field_name = property(get_field_name, set_field_name)
    parent = property(get_parent, set_parent)
    root = property(get_root, set_root)


class Field(BaseField):
    MESSAGES = {
        'required': 'This field is required.'
    }

    _NOT_READ_ONLY_WRITE_ONLY = 'May not set both `read_only` and `write_only`'
    _NOT_READ_ONLY_REQUIRED = 'May not set both `read_only` and `required`'
    _NOT_READ_ONLY_DEFAULT = 'May not set both `read_only` and `default`'
    _NOT_REQUIRED_DEFAULT = 'May not set both `required` and `default`'
    _MISSING_ERROR_MESSAGE = (
        'ValidationError raised by `{class_name}`, but error key `{key}` does '
        'not exist in the `MESSAGES` dictionary.'
    )

    def __init__(self, read_only=False, write_only=False,
                 required=None, default=empty, initial=None, source=None,
                 label=None, style=None):
        super(Field, self).__init__()

        # If `required` is unset, then use `True` unless a default is provided.
        if required is None:
            required = default is empty and not read_only

        # Some combinations of keyword arguments do not make sense.
        assert not (read_only and write_only), self._NOT_READ_ONLY_WRITE_ONLY
        assert not (read_only and required), self._NOT_READ_ONLY_REQUIRED
        assert not (read_only and default is not empty), self._NOT_READ_ONLY_DEFAULT
        assert not (required and default is not empty), self._NOT_REQUIRED_DEFAULT

        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.default = default
        self.source = source
        self.initial = initial
        self.label = label
        self.style = {} if style is None else style

    def setup(self, field_name, parent, root):
        """
        Setup the context for the field instance.
        """
        super(Field, self).setup(field_name, parent, root)
        if self.label is None:
            self.label = self.field_name.replace('_', ' ').capitalize()
        if self.source is None:
            self.source = field_name

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
        dictionary.set_field_item(self.field_name, value, field=self)

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
            self.fail('required')
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

    def fail(self, key, **kwargs):
        try:
            raise ValidationError(self.MESSAGES[key].format(**kwargs))
        except KeyError:
            class_name = self.__class__.__name__
            msg = self._MISSING_ERROR_MESSAGE.format(class_name=class_name, key=key)
            raise AssertionError(msg)


class BooleanField(Field):
    MESSAGES = {
        'required': 'This field is required.',
        'invalid_value': '`{input}` is not a valid boolean.'
    }

    def get_primitive_value(self, dictionary):
        if is_html_input(dictionary):
            # HTML forms do not send a `False` value on an empty checkbox,
            # so we override the default empty value to be False.
            return dictionary.get(self.field_name, False)
        return dictionary.get(self.field_name, empty)

    def to_native(self, data):
        if data in ('true', 't', 'True', '1', 1, True):
            return True
        elif data in ('false', 'f', 'False', '0', 0, 0.0, False):
            return False
        self.fail('invalid_value', input=data)


class CharField(Field):
    MESSAGES = {
        'required': 'This field is required.',
        'blank': 'This field may not be blank.'
    }

    def __init__(self, *args, **kwargs):
        self.allow_blank = kwargs.pop('allow_blank', False)
        super(CharField, self).__init__(*args, **kwargs)

    def to_native(self, data):
        if data == '' and not self.allow_blank:
            self.fail('blank')
        return str(data)


class ChoiceField(Field):
    MESSAGES = {
        'required': 'This field is required.',
        'invalid_choice': '`{input}` is not a valid choice.'
    }
    coerce_to_type = str

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')

        assert choices, '`choices` argument is required and may not be empty'

        # Allow either single or paired choices style:
        # choices = [1, 2, 3]
        # choices = [(1, 'First'), (2, 'Second'), (3, 'Third')]
        pairs = [
            isinstance(item, (list, tuple)) and len(item) == 2
            for item in choices
        ]
        if all(pairs):
            self.choices = {key: val for key, val in choices}
        else:
            self.choices = {item: item for item in choices}

        # Map the string representation of choices to the underlying value.
        # Allows us to deal with eg. integer choices while supporting either
        # integer or string input, but still get the correct datatype out.
        self.choice_strings_to_values = {
            str(key): key for key in self.choices.keys()
        }

        super(ChoiceField, self).__init__(*args, **kwargs)

    def to_native(self, data):
        try:
            return self.choice_strings_to_values[str(data)]
        except KeyError:
            self.fail('invalid_choice', input=data)


class MultipleChoiceField(ChoiceField):
    MESSAGES = {
        'required': 'This field is required.',
        'invalid_choice': '`{input}` is not a valid choice.',
        'not_a_list': 'Expected a list of items but got type `{input_type}`'
    }

    def to_native(self, data):
        if not hasattr(data, '__iter__'):
            self.fail('not_a_list', input_type=type(data).__name__)
        return set([
            super(MultipleChoiceField, self).to_native(item)
            for item in data
        ])


class IntegerField(Field):
    MESSAGES = {
        'required': 'This field is required.',
        'invalid_integer': 'A valid integer is required.'
    }

    def to_native(self, data):
        try:
            data = int(str(data))
        except (ValueError, TypeError):
            self.fail('invalid_integer')
        return data


class MethodField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(MethodField, self).__init__(**kwargs)

    def serialize(self, value):
        attr = 'get_{field_name}'.format(field_name=self.field_name)
        method = getattr(self.parent, attr)
        return method(value)
