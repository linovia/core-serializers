from collections import OrderedDict, namedtuple
import re


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


FieldResult = namedtuple('FieldResult', ['field', 'value', 'error'])


class FieldResultsDict(OrderedDict):
    """
    A dictionary class that additionally presents an interface for
    storing and retrieving the field instance that was used for each key.
    """

    def __init__(self, serializer):
        super(FieldResultsDict, self).__init__()
        self.field_results = []
        self.serializer = serializer

    def set_result(self, field, value, error=None):
        """
        Sets a key-value pair, additionally storing the field used.
        """
        self[field.field_name] = value
        self.field_results.append(FieldResult(field, value, error))

    def __repr__(self):
        return '<FieldResultsDict %s>' % dict.__repr__(self)


class ErrorResultsDict(OrderedDict):
    """
    A dictionary class that additionally presents an interface for
    storing and retrieving the field instance that was used for each key.
    """

    def __init__(self, serializer):
        super(ErrorResultsDict, self).__init__()
        self.field_results = []
        self.serializer = serializer

    def set_result(self, field, value, error=None):
        """
        Sets a key-value pair, additionally storing the field used.
        """
        self[field.field_name] = error
        self.field_results.append(FieldResult(field, value, error))

    def __repr__(self):
        return '<ErrorResultsDict %s>' % dict.__repr__(self)


def parse_html_list(dictionary, prefix=''):
    """
    Used to suport list values in HTML forms.
    Supports lists of primitives and/or dictionaries.

    * List of primitives.

    {
        '[0]': 'abc',
        '[1]': 'def',
        '[2]': 'hij'
    }
        -->
    [
        'abc',
        'def',
        'hij'
    ]

    * List of dictionaries.

    {
        '[0]foo': 'abc',
        '[0]bar': 'def',
        '[1]foo': 'hij',
        '[2]bar': 'klm',
    }
        -->
    [
        {'foo': 'abc', 'bar': 'def'},
        {'foo': 'hij', 'bar': 'klm'}
    ]
    """
    Dict = type(dictionary)
    ret = {}
    regex = re.compile(r'^%s\[([0-9]+)\](.*)$' % re.escape(prefix))
    for field, value in dictionary.items():
        match = regex.match(field)
        if not match:
            continue
        index, key = match.groups()
        index = int(index)
        if not key:
            ret[index] = value
        elif isinstance(ret.get(index), dict):
            ret[index][key] = value
        else:
            ret[index] = Dict({key: value})
    return [ret[item] for item in sorted(ret.keys())]


def parse_html_dict(dictionary, prefix):
    """
    Used to support dictionary values in HTML forms.

    {
        'profile.username': 'example',
        'profile.email': 'example@example.com',
    }
        -->
    {
        'profile': {
            'username': 'example,
            'email': 'example@example.com'
        }
    }
    """
    ret = {}
    regex = re.compile(r'^%s\.(.+)$' % re.escape(prefix))
    for field, value in dictionary.items():
        match = regex.match(field)
        if not match:
            continue
        key = match.groups()[0]
        ret[key] = value
    return ret
