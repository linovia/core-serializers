from core_serializers import fields
from core_serializers import serializers
import random


class TestSerializer:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            a = fields.Field()
            b = fields.Field()
        self.serializer = TestSerializer()

    def test_validate(self):
        data = {'a': 1, 'b': 2}
        assert data == self.serializer.validate(data)

    def test_create(self):
        data = {'a': 1, 'b': 2}
        obj = self.serializer.create(data)
        assert obj.a == 1
        assert obj.b == 2

    def test_update(self):
        obj = serializers.BasicObject(a=1, b=2)
        data = {'a': 3, 'b': 4}
        self.serializer.update(obj, data)
        assert obj.a == 3
        assert obj.b == 4


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
        validated = self.serializer.validate(data)
        assert validated['a'] == 'abc'
        assert validated['b'] == 1
        assert validated['c'] == True


def test_nested_serializer_not_required():
    class NestedSerializer(serializers.Serializer):
        b = fields.Field()
        c = fields.Field()

    class TestSerializer(serializers.Serializer):
        nested = NestedSerializer(required=False)
        a = fields.Field()

    data = {
        'a': random.randint(1, 10),
    }

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

        self.serializer = TestSerializer()

    def test_nested_validate(self):
        """
        A nested representation is validated into a flat internal object.
        """
        assert self.serializer.validate(self.data) == {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4
        }

    def test_nested_create(self):
        """
        A nested representation creates an object using the nested values.
        """
        obj = self.serializer.create(self.data)
        assert obj.a == 1
        assert obj.b == 2
        assert obj.c == 3
        assert obj.d == 4

    def test_nested_serialize(self):
        """
        An object can be serialized into a nested representation.
        """
        obj = serializers.BasicObject(a=1, b=2, c=3, d=4)
        assert self.serializer.serialize(obj) == self.data
