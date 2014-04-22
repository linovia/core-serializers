from core_serializers import serializers, fields, BasicObject
from core_serializers.fields import empty
from core_serializers.renderers import FormRenderer
import json


class ProfileSerializer(serializers.Serializer):
    email = fields.CharField()
    age = fields.IntegerField()
    admin = fields.BooleanField()

profile = BasicObject(email='tmp@example.com', age=23, admin=True)

serializer = ProfileSerializer()
data = serializer.serialize(profile)
FormRenderer().render(data)

print '---'
data = serializer.serialize()
FormRenderer().render(data)

print json.dumps(data)

#print serializer.serialize(empty)
    # def get_extras(self, request, *args, **kwargs):
    #     lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
    #     lookup = kwargs.get(lookup_url_kwarg, None)
    #     return {self.lookup_field: lookup}

    # def update(self, request, *args, **kwargs):
    #     self.object = self.get_object_or_none()
    #     extras = self.get_extras(request, *args, **kwargs)

    #     serializer = self.get_serializer()
    #     if self.object is None:
    #         self.object = serializer.create(request.data, extras=extras)
    #         status_code = status.HTTP_201_CREATED
    #     else:
    #         self.object = serializer.update(self.object, request.data, extras=extras)
    #         status_code = status.HTTP_200_OK

    #     data = serializer.serialize(self.object)
    #     return Response(data, status_code)
