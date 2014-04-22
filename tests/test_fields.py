from core_serializers import fields
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