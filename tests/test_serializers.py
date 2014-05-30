from core_serializers import fields, serializers
import pytest


class TestSerializer:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            a = fields.IntegerField()
            b = fields.IntegerField()
        self.Serializer = TestSerializer

    def test_validate(self):
        data = {'a': 1, 'b': 2}
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_create(self):
        data = {'a': 1, 'b': 2}
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.instance.a == 1
        assert serializer.instance.b == 2

    def test_update(self):
        data = {'a': 3, 'b': 4}
        obj = serializers.BasicObject(a=1, b=2)
        serializer = self.Serializer(obj, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.instance.a == 3
        assert serializer.instance.b == 4

    def test_missing_value(self):
        data = {'b': 2}
        serializer = self.Serializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'a': 'This field is required.'}

    def test_invalid_value(self):
        data = {'a': 'abc', 'b': 2}
        serializer = self.Serializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'a': 'A valid integer is required.'}


class TestSerializerWithTypedFields:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            a = fields.CharField()
            b = fields.IntegerField()
            c = fields.BooleanField()
        self.serializer = TestSerializer()

    def test_validate(self):
        """
        Typed fields are validated from the primative representation into
        their internal type.
        """
        data = {
            'a': 'abc',
            'b': '1',
            'c': 'true',
        }
        expected = {
            'a': 'abc',
            'b': 1,
            'c': True
        }
        validated = self.serializer.validate(data)
        assert validated == expected


def test_nested_serializer_not_required():
    class NestedSerializer(serializers.Serializer):
        b = fields.Field()
        c = fields.Field()

    class TestSerializer(serializers.Serializer):
        nested = NestedSerializer(required=False)
        a = fields.Field()

    data = {'a': 1}
    serializer = TestSerializer()
    assert data == serializer.validate(data)


# def test_nested_serializer_not_required_with_none():
#     class NestedSerializer(serializers.Serializer):
#         b = fields.Field()
#         c = fields.Field()

#     class TestSerializer(serializers.Serializer):
#         nested = NestedSerializer(required=False)
#         a = fields.Field()

#     data = {
#         'a': random.randint(1, 10),
#         'nested': None
#     }

#     serializer = TestSerializer()
#     assert data == serializer.validate(data)


class TestStarredSource:
    """
    Tests for `source='*'` argument, which is used for nested representations.

    For example:

        nested_field = NestedField(source='*')
    """
    data = {
        'nested1': {'a': 1, 'b': 2},
        'nested2': {'c': 3, 'd': 4}
    }

    def setup(self):
        class NestedSerializer1(serializers.Serializer):
            a = fields.Field()
            b = fields.Field()

        class NestedSerializer2(serializers.Serializer):
            c = fields.Field()
            d = fields.Field()

        class TestSerializer(serializers.Serializer):
            nested1 = NestedSerializer1(source='*')
            nested2 = NestedSerializer2(source='*')

        self.Serializer = TestSerializer

    def test_nested_validate(self):
        """
        A nested representation is validated into a flat internal object.
        """
        serializer = self.Serializer(data=self.data)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4
        }

    def test_nested_create(self):
        """
        A nested representation creates an object using the nested values.
        """
        serializer = self.Serializer(data=self.data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert obj.a == 1
        assert obj.b == 2
        assert obj.c == 3
        assert obj.d == 4

    def test_nested_serialize(self):
        """
        An object can be serialized into a nested representation.
        """
        obj = serializers.BasicObject(a=1, b=2, c=3, d=4)
        serializer = self.Serializer(obj)
        assert serializer.data == self.data
