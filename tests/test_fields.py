from core_serializers import fields, serializers
from core_serializers.utils import BasicObject
import pytest


class HTMLDict(dict):
    """
    A mock MultiDict that can be used for representing HTML input.
    """
    def getlist(self):
        pass  # pragma: no cover


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
        assert self.field.to_primative(123) == 123


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
        data = self.serializer.to_primative(obj)
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
        data = self.serializer.to_primative(obj)
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
        assert self.serializer.data == {
            'initial_field': 123,
            'blank_field': None
        }


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


class TestBooleanHTMLInput:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            archived = fields.BooleanField()
        self.serializer = TestSerializer()

    def test_empty_html_checkbox(self):
        """
        HTML checkboxes do not send any value, but should be treated
        as `False` by BooleanField.
        """
        data = HTMLDict()
        validated = self.serializer.validate(data)
        assert validated == {'archived': False}


class TestMethodField:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            example_method_field = fields.MethodField()

            def get_example_method_field(self, instance):
                return repr(instance)

        self.serializer = TestSerializer()

    def test_method_field(self):
        obj = serializers.BasicObject(a=1)
        assert self.serializer.to_primative(obj) == {
            'example_method_field': "<BasicObject 'a': 1>"
        }
