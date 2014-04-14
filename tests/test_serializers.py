from core_serializers import fields
from core_serializers import serializers
import random


def test_validate():
    class TestSerializer(serializers.Serializer):
        a = fields.Field()
        b = fields.Field()

    serializer = TestSerializer()
    data = {
        'a': random.randint(1, 10),
        'b': random.randint(1, 10)
    }

    assert data == serializer.validate(data)

def test_create():
    class TestSerializer(serializers.Serializer):
        a = fields.Field()
        b = fields.Field()

    serializer = TestSerializer()
    data = {
        'a': random.randint(1, 10),
        'b': random.randint(1, 10)
    }

    obj = serializer.create(data)
    assert obj.a == data['a']
    assert obj.b == data['b']


def test_update():
    class TestSerializer(serializers.Serializer):
        a = fields.Field()
        b = fields.Field()

    serializer = TestSerializer()
    obj = serializers.DeserializedObject(
        a=random.randint(1, 10),
        b=random.randint(1, 10)
    )
    data = {
        'a': random.randint(1, 10),
        'b': random.randint(1, 10)
    }

    serializer.update(obj, data)
    assert obj.a == data['a']
    assert obj.b == data['b']


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
    print validated, data
    assert validated['a'] == data['a']
    assert validated['b'] == int(data['b'])
    assert validated['c'] == (True if data['c'] == 'true' else False)


def test_nested_validate():
    class NestedSerializer(serializers.Serializer):
        b = fields.Field()
        c = fields.Field()

    class TestSerializer(serializers.Serializer):
        nested = NestedSerializer()
        a = fields.Field()

    data = {
        'a': random.randint(1, 10),
        'nested': {
            'b': random.randint(1, 10),
            'c': random.randint(1, 10),
        }
    }

    serializer = TestSerializer()
    assert data == serializer.validate(data)


def test_nested_create():
    class NestedSerializer(serializers.Serializer):
        b = fields.Field()
        c = fields.Field()

    class TestSerializer(serializers.Serializer):
        nested = NestedSerializer()
        a = fields.Field()

    data = {
        'a': random.randint(1, 10),
        'nested': {
            'b': random.randint(1, 10),
            'c': random.randint(1, 10),
        }
    }

    serializer = TestSerializer()
    obj = serializer.create(data)

    assert obj.a == data['a']
    assert obj.nested == data['nested']


def test_nested_update():
    class NestedSerializer(serializers.Serializer):
        b = fields.Field()
        c = fields.Field()

    class TestSerializer(serializers.Serializer):
        nested = NestedSerializer()
        a = fields.Field()

    obj = serializers.DeserializedObject(
        a=random.randint(1, 10),
        nested={
            'b': random.randint(1, 10),
            'c': random.randint(1, 10)
        }
    )
    data = {
        'a': random.randint(1, 10),
        'nested': {
            'b': random.randint(1, 10),
            'c': random.randint(1, 10),
        }
    }

    serializer = TestSerializer()
    serializer.update(obj, data)

    assert obj.a == data['a']
    assert obj.nested == data['nested']


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
        obj = serializers.DeserializedObject(
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
        obj = serializers.DeserializedObject(
            username = 'abcdefghijklmnopqrstuvwzyz'
        )
        assert serializer.serialize(obj) == {
            'username': 'abcdefghijklmnopqrstuvwzyz',
            'class_name': 'DeserializedObject'
        }