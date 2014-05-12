from core_serializers import fields
from core_serializers.fields import ValidationError
import copy
import pytest


class ValidAndInvalidValues:
    """
    Base class for testing valid and invalid values on a field.
    """

    def setup(self):
        self.field = copy.copy(self.base_field)

    def test_valid_values(self):
        """
        Valid input should validate as a boolean.
        """
        for input_value, expected_output in self.expected_mappings.items():
            assert self.field.validate(input_value) == expected_output

    def test_invalid_values(self):
        for input_value, expected_failure in self.invalid_mappings.items():
            with pytest.raises(ValidationError) as exc_info:
                self.field.validate(input_value)
            assert str(exc_info.value) == expected_failure


class TestCharField(ValidAndInvalidValues):
    expected_mappings = {
        1: '1',
        'abc': 'abc'
    }

    invalid_mappings = {
        '': 'This field may not be blank.'
    }

    base_field = fields.CharField()


class TestBooleanField(ValidAndInvalidValues):
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

    invalid_mappings = {
        'foo': '`foo` is not a valid boolean.'
    }

    base_field = fields.BooleanField()


class TestChoiceField(ValidAndInvalidValues):
    expected_mappings = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }

    invalid_mappings = {
        'awful': '`awful` is not a valid choice.'
    }

    base_field = fields.ChoiceField(
        choices=[
            ('poor', 'Poor quality'),
            ('medium', 'Medium quality'),
            ('good', 'Good quality'),
        ]
    )


class TestChoiceFieldWithType(ValidAndInvalidValues):
    expected_mappings = {
        '1': 1,
        3: 3,
    }

    invalid_mappings = {
        5: '`5` is not a valid choice.',
        'abc': 'Expected type `int` but got type `str`.'
    }

    # This choice field that uses a non-string type for the valid choices.
    base_field = fields.ChoiceField(
        choices=[
            (1, 'Poor quality'),
            (2, 'Medium quality'),
            (3, 'Good quality'),
        ],
        type=int
    )


class TestChoiceFieldWithListChoices(ValidAndInvalidValues):
    expected_mappings = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }

    invalid_mappings = {
        'awful': '`awful` is not a valid choice.'
    }

    # This choice field uses a list of items as choices, instead of a 2-tuple.
    base_field = fields.ChoiceField(choices=('poor', 'medium', 'good'))


class TestMultipleChoiceField(ValidAndInvalidValues):
    expected_mappings = {
        (): set(),
        ('aircon',): set(['aircon']),
        ('aircon', 'manual'): set(['aircon', 'manual']),
    }

    invalid_mappings = {
        'abc': 'Expected a list of items but got type `str`',
        ('aircon', 'incorrect'): '`incorrect` is not a valid choice.'
    }

    base_field = fields.MultipleChoiceField(
        choices=[
            ('aircon', 'AirCon'),
            ('manual', 'Manual drive'),
            ('diesel', 'Diesel'),
        ]
    )


class TestIntegerField(ValidAndInvalidValues):
    expected_mappings = {
        '1': 1,
        '0': 0,
        1: 1,
        0: 0,
    }

    invalid_mappings = {
        'abc': 'A valid integer is required.'
    }

    base_field = fields.IntegerField()
