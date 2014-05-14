from core_serializers import fields, serializers
from core_serializers.utils import BasicObject
import pytest


class TestBaseField:
    def setup(self):
        self.field = fields.BaseField()

    def test_validate(self):
        """
        By default a field should simply return the data it validates.
        """
        assert self.field.validate(123) == 123

    def test_serialize(self):
        """
        By default a field should simply return the data it serializes.
        """
        assert self.field.serialize(123) == 123


class TestBaseFieldUsedInSerializer:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            field = fields.BaseField()
        self.serializer = TestSerializer()

    def test_validate(self):
        """
        By default the base field should simply return the data it validates.
        """
        data = {'field': 123}
        assert self.serializer.validate(data) == data

    def test_serialize(self):
        """
        By default a base field should simply return the data it serializes.
        """
        obj = BasicObject(field=123)
        expected = {'field': 123}
        assert self.serializer.serialize(obj) == expected


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
        with pytest.raises(fields.ValidationError):
            assert self.field.validate()

    def test_serialize(self):
        """
        By default a field should simply return the data it serializes.
        """
        assert self.field.serialize(123) == 123


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
        assert validated == {'default': 123, 'no_default': 456}

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
            labeled = fields.IntegerField(label='My label')
        self.serializer = TestSerializer()

    def test_label(self):
        """
        A field's label may be set with the `label` argument.
        """
        fields = self.serializer.fields
        assert fields['labeled'].label == 'My label'


class TestInvalidErrorKey:
    def setup(self):
        class ExampleField(serializers.Field):
            def to_native(self, data):
                self.fail('incorrect')
        self.field = ExampleField()

    def test_invalid_error_key(self):
        """
        If a field raises a validation error, but does not have a corresponding
        error message, then raise an appropriate assertion error.
        """
        with pytest.raises(AssertionError) as exc_info:
            self.field.to_native(123)
        expected = (
            'ValidationError raised by `ExampleField`, but error key '
            '`incorrect` does not exist in the `MESSAGES` dictionary.'
        )
        assert str(exc_info.value) == expected


class TestUnboundAccess:
    def setup(self):
        self.field = fields.IntegerField(label='My label')

    def test_unbound_access(self):
        """
        Attempting to get bind-time attributes on an unbound field will error.
        """
        for attr in ('field_name', 'parent', 'root'):
            with pytest.raises(AssertionError) as exc_info:
                getattr(self.field, attr)
            expected = (
                'Cannot access attribute `{attr}` on field `IntegerField`. '
                'The field has not yet been bound to a serializer.'
            ).format(attr=attr)
            assert str(exc_info.value) == expected


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
