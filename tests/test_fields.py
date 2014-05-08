from core_serializers import fields, serializers, BasicObject
from core_serializers.fields import empty, ValidationError
import pytest


class TestField:
    def setup(self):
        self.field = fields.Field()

    def test_validate(self):
        """
        By default a field should simply return the data it validates.
        """
        assert self.field.validate(123) == 123

    def test_validate_no_data(self):
        """
        By default a field should raise a ValidationError if no data is
        passed to it when validating.
        """
        with pytest.raises(ValidationError):
            assert self.field.validate()

    def test_serialize(self):
        """
        By default a field should simply return the data it serializes.
        """
        assert self.field.serialize(123) == 123


# Tests for field options

class TestNotRequired:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            optional = fields.IntegerField(required=False)
            mandatory = fields.IntegerField()
        self.serializer = TestSerializer()

    def test_validate_read_only(self):
        """
        Non-required fields may be omitted in validation.
        """
        data = {'mandatory': 123}
        validated = self.serializer.validate(data)
        assert validated == {'mandatory': 123}


class TestReadOnly:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            read_only = fields.Field(read_only=True)
            writable = fields.IntegerField()
        self.serializer = TestSerializer()

    def test_validate_read_only(self):
        """
        Read-only fields should not be included in validation.
        """
        data = {'read_only': 123, 'writable': 456}
        validated = self.serializer.validate(data)
        assert validated == {'writable': 456}

    def test_serialize_read_only(self):
        """
        Read-only fields should be serialized.
        """
        obj = BasicObject(read_only=123, writable=456)
        data = self.serializer.serialize(obj)
        assert data == {'read_only': 123, 'writable': 456}


class TestWriteOnly:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            write_only = fields.IntegerField(write_only=True)
            readable = fields.IntegerField()
        self.serializer = TestSerializer()

    def test_validate_write_only(self):
        """
        Write-only fields should be included in validation.
        """
        data = {'write_only': 123, 'readable': 456}
        validated = self.serializer.validate(data)
        assert validated == {'write_only': 123, 'readable': 456}

    def test_serialize_write_only(self):
        """
        Write-only fields should not be serialized.
        """
        obj = BasicObject(write_only=123, readable=456)
        data = self.serializer.serialize(obj)
        assert data == {'readable': 456}


class TestDefault:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            default = fields.IntegerField(default=123)
            no_default = fields.IntegerField()
        self.serializer = TestSerializer()

    def test_validate_default(self):
        """
        A default value should be used if no value is passed in validation.
        """
        data = {'no_default': 456}
        validated = self.serializer.validate(data)
        assert validated == {'default':123, 'no_default': 456}

    def test_validate_default_not_used(self):
        """
        A default value should not be used if a value is passed in validation.
        """
        data = {'default': 0, 'no_default': 456}
        validated = self.serializer.validate(data)
        assert validated == {'default': 0, 'no_default': 456}


class TestInitial:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            initial_field = fields.IntegerField(initial=123)
            blank_field = fields.IntegerField()
        self.serializer = TestSerializer()

    def test_initial(self):
        """
        Initial values should be included when serializing a new representation.
        """
        data = self.serializer.serialize()
        assert data == {'initial_field': 123, 'blank_field': None}


class TestLabel:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            unlabeled = fields.IntegerField()
            labeled = fields.IntegerField(label='My label')
        self.serializer = TestSerializer()

    def test_default_label_is_field_name(self):
        """
        If unset, then a field's default label is the same as it's field name.
        """
        fields = self.serializer.fields
        assert fields['unlabeled'].label == 'unlabeled'

    def test_explicit_label(self):
        """
        A field's label may be explicitly set with the `label` argument.
        """
        fields = self.serializer.fields
        assert fields['labeled'].label == 'My label'

# Tests for typed fields

class TestCharField:
    expected_mappings = {
        1: '1',
        'abc': 'abc'
    }

    def setup(self):
        self.field = fields.CharField()

    def test_valid_values(self):
        """
        Valid input should validate as a boolean.
        """
        for input_value, expected_output in self.expected_mappings.items():
            assert self.field.validate(input_value) == expected_output

    def test_blank(self):
        """
        Blank input should raise a validation error.
        """
        with pytest.raises(ValidationError) as exc_info:
            self.field.validate('')
        assert str(exc_info.value) == 'This field may not be blank.'


class TestBooleanField:
    expected_mappings = {
        'true': True,
        'false': False,
        '1': True,
        '0': False,
        1: True,
        0: False,
        True: True,
        False: False,
    }

    def setup(self):
        self.field = fields.BooleanField()

    def test_valid_values(self):
        """
        Valid input should validate as a boolean.
        """
        for input_value, expected_output in self.expected_mappings.items():
            assert self.field.validate(input_value) == expected_output


class TestIntegerField:
    expected_mappings = {
        '1': 1,
        '0': 0,
        1: 1,
        0: 0,
    }

    def setup(self):
        self.field = fields.IntegerField()

    def test_valid_values(self):
        """
        Valid input should validate as an integer.
        """
        for input_value, expected_output in self.expected_mappings.items():
            assert self.field.validate(input_value) == expected_output

    def test_invalid_value(self):
        """
        Invalid input should raise a validation error.
        """
        with pytest.raises(ValidationError) as exc_info:
            self.field.validate('abc')
        assert str(exc_info.value) == 'A valid integer is required.'


# Tests for complex fields

class TestMethodField:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            example_method_field = fields.MethodField()

            def get_example_method_field(self, instance):
                return repr(instance)

        self.serializer = TestSerializer()

    def test_method_field(self):
        obj = serializers.BasicObject(a=1)
        assert self.serializer.serialize(obj) == {
            'example_method_field': "<BasicObject 'a': 1>"
        }
