from collections import OrderedDict


class BasicObject(object):
    """
    A basic object that simply sets whatever attributes are
    passed to it at initialization.

    The default Serializer class uses this on `create()`.
    """

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value) 

    def __repr__(self):
        attributes = str(self.__dict__).lstrip('{').rstrip('}')
        return '<BasicObject %s>' % attributes

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class FieldDict(OrderedDict):
    """
    A dictionary class that can additionally presents an interface for
    storing and retrieving the field instance that was used for each key.
    """

    def __init__(self):
        super(FieldDict, self).__init__()
        self._fields = {}

    def set_item(self, key, value, field):
        self[key] = value
        self._fields[key] = field

    def field_items(self):
        for key, value in self.items():
            yield key, value, self._fields[key]
