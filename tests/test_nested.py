from core_serializers import serializers, fields, BasicObject
from werkzeug import MultiDict


class TestListSerializer:
    def setup(self):
        class NestedSerializer(serializers.Serializer):
            one = fields.IntegerField()
            two = fields.IntegerField()

        class TestSerializer(serializers.Serializer):
            nested = NestedSerializer()

        self.serializer = TestSerializer()

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
        assert self.serializer.validate(input_data) == expected_data

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
        assert self.serializer.create(input_data) == expected_object


    def test_nested_update(self):
        update_object = serializers.BasicObject(
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
        self.serializer.update(update_object, input_data)
        assert update_object == expected_object

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
        assert self.serializer.validate(input_data) == expected_data