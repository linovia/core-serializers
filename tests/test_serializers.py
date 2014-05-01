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


def test_value_serializer():
    class TestSerializer(serializers.Serializer):
        a = fields.CharField()
        b = fields.IntegerField()
        c = fields.BooleanField()

    serializer = TestSerializer()
    data = {
        'a': random.choice('abcdefghijklmnopqrstuvwxyz'),
        'b': str(random.randint(1, 10)),
        'c': random.choice(['true', 'false']),
    }

    validated = serializer.validate(data)
    assert validated['a'] == data['a']
    assert validated['b'] == int(data['b'])
    assert validated['c'] == (True if data['c'] == 'true' else False)


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
    data = {
        'nested1': {
            'a': random.randint(1, 10),
            'b': random.randint(1, 10),
        },
        'nested2': {
            'c': random.randint(1, 10),
            'd': random.randint(1, 10),
        }
    }

    def get_serializer(self):
        class NestedSerializer1(serializers.Serializer):
            a = fields.Field()
            b = fields.Field()

        class NestedSerializer2(serializers.Serializer):
            c = fields.Field()
            d = fields.Field()

        class TestSerializer(serializers.Serializer):
            nested1 = NestedSerializer1(source='*')
            nested2 = NestedSerializer2(source='*')

        return TestSerializer()

    def test_nested_validate(self):
        serializer = self.get_serializer()
        assert serializer.validate(self.data) == {
            'a': self.data['nested1']['a'],
            'b': self.data['nested1']['b'],
            'c': self.data['nested2']['c'],
            'd': self.data['nested2']['d']
        }

    def test_nested_create(self):
        serializer = self.get_serializer()
        obj = serializer.create(self.data)
        assert obj.a == self.data['nested1']['a']
        assert obj.b == self.data['nested1']['b']
        assert obj.c == self.data['nested2']['c']
        assert obj.d == self.data['nested2']['d']

    def test_nested_serialize(self):
        serializer = self.get_serializer()
        obj = serializers.BasicObject(
            a=self.data['nested1']['a'],
            b=self.data['nested1']['b'],
            c=self.data['nested2']['c'],
            d=self.data['nested2']['d']
        )
        assert serializer.serialize(obj) == self.data


class TestMethodField:
    def get_serializer(self):
        class TestSerializer(serializers.Serializer):
            username = fields.Field()
            class_name = fields.MethodField()

            def get_class_name(self, instance):
                return instance.__class__.__name__

        return TestSerializer()

    def test_method_field(self):
        serializer = self.get_serializer()
        obj = serializers.BasicObject(
            username = 'abcdefghijklmnopqrstuvwzyz'
        )
        assert serializer.serialize(obj) == {
            'username': 'abcdefghijklmnopqrstuvwzyz',
            'class_name': 'BasicObject'
        }