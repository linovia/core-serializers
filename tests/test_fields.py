from core_serializers import fields, serializers
from core_serializers.fields import empty
import random


def test_validate():
    """
    By default a field should simply return the data it validates.
    """
    num = random.randint(1, 10)
    field = fields.Field()
    assert field.validate(num) == num

def test_validate_no_data():
    """
    By default a field should simply return the data it validates.
    """
    num = random.randint(1, 10)
    field = fields.Field(required=False)
    assert field.validate(empty) == empty

def test_read_only_field():
    """
    A read-only field should always return empty data when validating.
    """
    num = random.randint(1, 10)
    field = fields.Field(read_only=True)
    assert field.validate(num) == empty

def test_default_field():
    """
    A field with a default value should return it when validating empty data.
    """
    num = random.randint(1, 10)
    field = fields.Field(default=num)
    assert field.validate(empty) == num

def test_serialize():
    """
    By default a field should simply return the data it serializes.
    """
    num = random.randint(1, 10)
    field = fields.Field()
    assert field.serialize(num) == num

def test_write_only_field():
    """
    A write-only field should always return empty data when serializing.
    """
    num = random.randint(1, 10)
    field = fields.Field(write_only=True)
    assert field.serialize(num) == empty


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
