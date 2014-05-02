from core_serializers import fields, serializers
from core_serializers.fields import empty, ValidationError
import pytest


def test_validate():
    """
    By default a field should simply return the data it validates.
    """
    field = fields.Field()
    assert field.validate(123) == 123

def test_validate_no_data():
    """
    By default a field should raise a ValidationError if no data is
    passed to it when validating.
    """
    field = fields.Field()
    with pytest.raises(ValidationError):
        assert field.validate()

def test_field_not_required():
    """
    A field with `required=False` should not raise validation errors if
    not passed any value to validate.
    """
    field = fields.Field(required=False)
    assert field.validate() == empty

def test_read_only_field():
    """
    A read-only field should always return empty data when validating.
    """
    field = fields.Field(read_only=True)
    assert field.validate(123) == empty

def test_default_field():
    """
    A field with a default value should return it when validating empty data.
    """
    field = fields.Field(default=123)
    assert field.validate() == 123

def test_serialize():
    """
    By default a field should simply return the data it serializes.
    """
    field = fields.Field()
    assert field.serialize(123) == 123

def test_initial_field():
    """
    A field with an initial value should return it when serializing empty data.
    """
    field = fields.Field(initial=123)
    field.setup('', None, None)
    assert field.get_native_value() == 123

def test_write_only_field():
    """
    A write-only field should always return empty data when serializing.
    """
    field = fields.Field(write_only=True)
    assert field.serialize(123) == empty

class TestInitialValue:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            field = fields.IntegerField(initial=123)
        self.serializer = TestSerializer()

    def test_initial(self):
        data = self.serializer.serialize()
        assert data == {'field': 123}


# Tests for typed fields

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
