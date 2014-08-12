
import pytest
from collections import OrderedDict

from django.contrib.auth.models import User
from core_serializers.django import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User


def test_find_fields():
    serializer = UserSerializer()
    fields = serializer.get_fields()
    assert fields.keys() == []


def create_user():
    user_data = OrderedDict((
        ('username', 'johndoe'),
        ('first_name', 'John'),
        ('last_name', 'Doe'),
        ('email', 'johndoe@gmail.com'),
    ))
    return user_data, User.objects.create(**user_data)    


@pytest.mark.django_db
def test_model_serialization():
    user_data, user = create_user()
    serializer = UserSerializer(instance=user)
    assert serializer.data == user_data
