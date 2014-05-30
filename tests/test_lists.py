from core_serializers import serializers, fields
from core_serializers.utils import BasicObject
from werkzeug import MultiDict


class TestListSerializer:
    """
    Tests for using a ListSerializer as a top-level serializer.
    Note that this is in contrast to using ListSerializer as a field.
    """

    def setup(self):
        self.serializer = serializers.ListSerializer(child=fields.IntegerField())

    def test_validate(self):
        """
        Validating a list of items should return a list of validated items.
        """
        input_data = ["123", "456"]
        expected_output = [123, 456]
        assert self.serializer.validate(input_data) == expected_output

    def test_validate_html_input(self):
        """
        HTML input should be able to mock list structures using [x] style ids.
        """
        input_data = MultiDict({"[0]": "123", "[1]": "456"})
        expected_output = [123, 456]
        assert self.serializer.validate(input_data) == expected_output


class TestListSerializerContainingNestedSerializer:
    """
    Tests for using a ListSerializer containing another serializer.
    """

    def setup(self):
        class TestSerializer(serializers.Serializer):
            integer = fields.IntegerField()
            boolean = fields.BooleanField()

        self.serializer = serializers.ListSerializer(TestSerializer())

    def test_validate(self):
        """
        Validating a list of dictionaries should return a list of
        validated dictionaries.
        """
        input_data = [
            {"integer": "123", "boolean": "true"},
            {"integer": "456", "boolean": "false"}
        ]
        expected_output = [
            {"integer": 123, "boolean": True},
            {"integer": 456, "boolean": False}
        ]
        assert self.serializer.validate(input_data) == expected_output

    def test_create(self):
        """
        Creating from a list of dictionaries should return a list of objects.
        """
        input_data = [
            {"integer": "123", "boolean": "true"},
            {"integer": "456", "boolean": "false"}
        ]
        expected_output = [
            BasicObject(integer=123, boolean=True),
            BasicObject(integer=456, boolean=False),
        ]
        assert self.serializer.create(input_data) == expected_output

    def test_serialize(self):
        """
        Serialization of a list of objects should return a list of dictionaries.
        """
        input_objects = [
            BasicObject(integer=123, boolean=True),
            BasicObject(integer=456, boolean=False)
        ]
        expected_output = [
            {"integer": 123, "boolean": True},
            {"integer": 456, "boolean": False}
        ]
        assert self.serializer.serialize(input_objects) == expected_output

    def test_validate_html_input(self):
        """
        HTML input should be able to mock list structures using [x]
        style prefixes.
        """
        input_data = MultiDict({
            "[0]integer": "123",
            "[0]boolean": "true",
            "[1]integer": "456",
            "[1]boolean": "false"
        })
        expected_output = [
            {"integer": 123, "boolean": True},
            {"integer": 456, "boolean": False}
        ]
        assert self.serializer.validate(input_data) == expected_output


class TestNestedListSerializer:
    """
    Tests for using a ListSerializer as a field.
    """

    def setup(self):
        class TestSerializer(serializers.Serializer):
            integers = serializers.ListSerializer(fields.IntegerField())
            booleans = serializers.ListSerializer(fields.BooleanField())

        self.serializer = TestSerializer()

    def test_validate(self):
        """
        Validating a list of items should return a list of validated items.
        """
        input_data = {
            "integers": ["123", "456"],
            "booleans": ["true", "false"]
        }
        expected_output = {
            "integers": [123, 456],
            "booleans": [True, False]
        }
        assert self.serializer.validate(input_data) == expected_output

    def test_create(self):
        """
        Creation with a list of items return an object with an attribute that
        is a list of items.
        """
        input_data = {
            "integers": ["123", "456"],
            "booleans": ["true", "false"]
        }
        expected_output = BasicObject(
            integers=[123, 456],
            booleans=[True, False]
        )
        assert self.serializer.create(input_data) == expected_output

    def test_serialize(self):
        """
        Serialization of a list of items should return a list of items.
        """
        input_object = BasicObject(
            integers=[123, 456],
            booleans=[True, False]
        )
        expected_output = {
            "integers": [123, 456],
            "booleans": [True, False]
        }
        assert self.serializer.serialize(input_object) == expected_output

    def test_validate_html_input(self):
        """
        HTML input should be able to mock list structures using [x]
        style prefixes.
        """
        input_data = MultiDict({
            "integers[0]": "123",
            "integers[1]": "456",
            "booleans[0]": "true",
            "booleans[1]": "false"
        })
        expected_output = {
            "integers": [123, 456],
            "booleans": [True, False]
        }
        assert self.serializer.validate(input_data) == expected_output


class TestNestedListOfListsSerializer:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            integers = serializers.ListSerializer(
                serializers.ListSerializer(
                    fields.IntegerField()
                )
            )
            booleans = serializers.ListSerializer(
                serializers.ListSerializer(
                    fields.BooleanField()
                )
            )

        self.serializer = TestSerializer()

    def test_validate(self):
        input_data = {
            'integers': [['123', '456'], ['789', '0']],
            'booleans': [['true', 'true'], ['false', 'true']]
        }
        expected_output = {
            "integers": [[123, 456], [789, 0]],
            "booleans": [[True, True], [False, True]]
        }
        assert self.serializer.validate(input_data) == expected_output

    def test_validate_html_input(self):
        """
        HTML input should be able to mock lists of lists using [x][y]
        style prefixes.
        """
        input_data = MultiDict({
            "integers[0][0]": "123",
            "integers[0][1]": "456",
            "integers[1][0]": "789",
            "integers[1][1]": "000",
            "booleans[0][0]": "true",
            "booleans[0][1]": "true",
            "booleans[1][0]": "false",
            "booleans[1][1]": "true"
        })
        expected_output = {
            "integers": [[123, 456], [789, 0]],
            "booleans": [[True, True], [False, True]]
        }
        assert self.serializer.validate(input_data) == expected_output
