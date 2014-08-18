
import pytest
from collections import OrderedDict

from django.contrib.auth.models import User
import core_serializers.serializers
from core_serializers.django import serializers


class FullUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        extra_arguments = {
            'id': 'read_only',
        }


def test_metaclass_get_default_fields():
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
    name = 'DemoSerializer'
    bases = (
        serializers.ModelSerializer,
    )
    attrs = {
        'Meta': Meta
    }
    serializers.ModelSerializerMetaclass(name, bases, attrs)
    assert set(attrs['_fields'].keys()) == set(['first_name', 'last_name'])


def create_user():
    user_data = dict((
        ('username', 'johndoe'),
        ('first_name', 'John'),
        ('last_name', 'Doe'),
        ('email', 'johndoe@gmail.com'),
    ))
    return user_data, User.objects.create(**user_data)    


@pytest.mark.django_db
def test_model_serialization():
    user_data, user = create_user()
    serializer = FullUserSerializer(instance=user)
    ordered_fields = ['id', 'password', 'last_login', 'is_superuser',
        'username', 'first_name', 'last_name', 'email', 'is_staff',
        'is_active', 'date_joined']
    expected_data = OrderedDict((k, getattr(user, k)) for k in ordered_fields)
    assert serializer.data == expected_data


@pytest.mark.django_db
def test_model_deserialization():
    data = {
        'username': 'johndoe',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@doe.org'
    }
    serializer = UserSerializer(data=data)
    assert serializer.is_valid()
    instance = serializer.save()#commit=False)
    assert instance
    assert isinstance(instance, User)
    assert instance.id == 1
