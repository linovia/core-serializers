from core_serializers import serializers, fields
from core_serializers.utils import BasicObject
from werkzeug import MultiDict


class TestListSerializer:
    def setup(self):
        class NestedSerializer(serializers.Serializer):
            one = fields.IntegerField()
            two = fields.IntegerField()

        class TestSerializer(serializers.Serializer):
            nested = NestedSerializer()

        self.Serializer = TestSerializer

    def test_nested_validate(self):
        input_data = {
            'nested': {
                'one': '1',
                'two': '2',
            }
        }
        expected_data = {
            'nested': {
                'one': 1,
                'two': 2,
            }
        }
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_data

    def test_nested_create(self):
        input_data = {
            'nested': {
                'one': '1',
                'two': '2',
            }
        }
        expected_object = BasicObject(
            nested={
                'one': 1,
                'two': 2,
            }
        )
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert obj == expected_object

    def test_nested_update(self):
        obj = serializers.BasicObject(
            nested={
                'one': 1,
                'two': 2
            }
        )
        input_data = {
            'nested': {
                'one': "3",
                'two': "4",
            }
        }
        expected_object = BasicObject(
            nested={
                'one': 3,
                'two': 4,
            }
        )
        serializer = self.Serializer(obj, data=input_data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert obj == expected_object

    def test_nested_validate_html_input(self):
        input_data = MultiDict({
            'nested.one': '1',
            'nested.two': '2',
        })
        expected_data = {
            'nested': {
                'one': 1,
                'two': 2,
            }
        }
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_data

    def test_nested_serialize_empty(self):
        expected_data = {
            'nested': {
                'one': None,
                'two': None
            }
        }
        serializer = self.Serializer()
        assert serializer.data == expected_data
