from core_serializers.compat import (
    iterkeys, itervalues, iteritems, iterlists,
    iter_multi_items, native_itermethods
)
from collections import defaultdict, OrderedDict
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


class FieldDict(OrderedDict):
    """
    A dictionary class that can additionally presents an interface for
    storing and retrieving the field instance that was used for each key.
    """

    def __init__(self):
        super(FieldDict, self).__init__()
        self._fields = {}

    def set_item(self, key, value, field):
        """
        Sets a key-value pair, additionally storing the field used.
        """
        self[key] = value
        self._fields[key] = field

    def field_items(self):
        """
        Returns a three-tuple of (key, value, field) for each item.
        """
        for key, value in self.items():
            yield key, value, self._fields[key]

    def __repr__(self):
        return '<FieldDict %s>' % dict.__repr__(self)


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
            ret[index] = MultiDict({key: value})
    return [ret[key] for key in sorted(ret.keys())]


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


class _Missing(object):

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

_missing = _Missing()


@native_itermethods(['keys', 'values', 'items', 'lists', 'listvalues'])
class MultiDict(dict):
    """A :class:`MultiDict` is a dictionary subclass customized to deal with
    multiple values for the same key which is for example used by the parsing
    functions in the wrappers.  This is necessary because some HTML form
    elements pass multiple values for the same key.

    :class:`MultiDict` implements all standard dictionary methods.
    Internally, it saves all values for a key as a list, but the standard dict
    access methods will only return the first value for a key. If you want to
    gain access to the other values, too, you have to use the `list` methods as
    explained below.

    Basic Usage:

    >>> d = MultiDict([('a', 'b'), ('a', 'c')])
    >>> d
    MultiDict([('a', 'b'), ('a', 'c')])
    >>> d['a']
    'b'
    >>> d.getlist('a')
    ['b', 'c']
    >>> 'a' in d
    True

    It behaves like a normal dict thus all dict functions will only return the
    first value when multiple values for one key are found.

    A :class:`MultiDict` can be constructed from an iterable of
    ``(key, value)`` tuples, a dict, a :class:`MultiDict` or from Werkzeug 0.2
    onwards some keyword parameters.

    :param mapping: the initial value for the :class:`MultiDict`.  Either a
                    regular dict, an iterable of ``(key, value)`` tuples
                    or `None`.
    """

    def __init__(self, mapping=None):
        if isinstance(mapping, MultiDict):
            dict.__init__(self, ((k, l[:]) for k, l in iterlists(mapping)))
        elif isinstance(mapping, dict):
            tmp = {}
            for key, value in iteritems(mapping):
                if isinstance(value, (tuple, list)):
                    value = list(value)
                else:
                    value = [value]
                tmp[key] = value
            dict.__init__(self, tmp)
        else:
            tmp = {}
            for key, value in mapping or ():
                tmp.setdefault(key, []).append(value)
            dict.__init__(self, tmp)

    def __getstate__(self):
        return dict(self.lists())

    def __setstate__(self, value):
        dict.clear(self)
        dict.update(self, value)

    def __getitem__(self, key):
        """Return the first data value for this key;
        raises KeyError if not found.

        :param key: The key to be looked up.
        :raise KeyError: if the key does not exist.
        """
        if key in self:
            return dict.__getitem__(self, key)[0]
        raise KeyError(key)

    def __setitem__(self, key, value):
        """Like :meth:`add` but removes an existing key first.

        :param key: the key for the value.
        :param value: the value to set.
        """
        dict.__setitem__(self, key, [value])

    def add(self, key, value):
        """Adds a new value for the key.

        .. versionadded:: 0.6

        :param key: the key for the value.
        :param value: the value to add.
        """
        dict.setdefault(self, key, []).append(value)

    def get(self, key, default=None, type=None):
        """Return the default value if the requested data doesn't exist.
        If `type` is provided and is a callable it should convert the value,
        return it or raise a :exc:`ValueError` if that is not possible.  In
        this case the function will return the default as if the value was not
        found:

        >>> d = TypeConversionDict(foo='42', bar='blub')
        >>> d.get('foo', type=int)
        42
        >>> d.get('bar', -1, type=int)
        -1

        :param key: The key to be looked up.
        :param default: The default value to be returned if the key can't
                        be looked up.  If not further specified `None` is
                        returned.
        :param type: A callable that is used to cast the value in the
                     :class:`MultiDict`.  If a :exc:`ValueError` is raised
                     by this callable the default value is returned.
        """
        try:
            rv = self[key]
            if type is not None:
                rv = type(rv)
        except (KeyError, ValueError):
            rv = default
        return rv

    def getlist(self, key, type=None):
        """Return the list of items for a given key. If that key is not in the
        `MultiDict`, the return value will be an empty list.  Just as `get`
        `getlist` accepts a `type` parameter.  All items will be converted
        with the callable defined there.

        :param key: The key to be looked up.
        :param type: A callable that is used to cast the value in the
                     :class:`MultiDict`.  If a :exc:`ValueError` is raised
                     by this callable the value will be removed from the list.
        :return: a :class:`list` of all the values for the key.
        """
        try:
            rv = dict.__getitem__(self, key)
        except KeyError:
            return []
        if type is None:
            return list(rv)
        result = []
        for item in rv:
            try:
                result.append(type(item))
            except ValueError:
                pass
        return result

    def setlist(self, key, new_list):
        """Remove the old values for a key and add new ones.  Note that the list
        you pass the values in will be shallow-copied before it is inserted in
        the dictionary.

        >>> d = MultiDict()
        >>> d.setlist('foo', ['1', '2'])
        >>> d['foo']
        '1'
        >>> d.getlist('foo')
        ['1', '2']

        :param key: The key for which the values are set.
        :param new_list: An iterable with the new values for the key.  Old values
                         are removed first.
        """
        dict.__setitem__(self, key, list(new_list))

    def setdefault(self, key, default=None):
        """Returns the value for the key if it is in the dict, otherwise it
        returns `default` and sets that value for `key`.

        :param key: The key to be looked up.
        :param default: The default value to be returned if the key is not
                        in the dict.  If not further specified it's `None`.
        """
        if key not in self:
            self[key] = default
        else:
            default = self[key]
        return default

    def setlistdefault(self, key, default_list=None):
        """Like `setdefault` but sets multiple values.  The list returned
        is not a copy, but the list that is actually used internally.  This
        means that you can put new values into the dict by appending items
        to the list:

        >>> d = MultiDict({"foo": 1})
        >>> d.setlistdefault("foo").extend([2, 3])
        >>> d.getlist("foo")
        [1, 2, 3]

        :param key: The key to be looked up.
        :param default: An iterable of default values.  It is either copied
                        (in case it was a list) or converted into a list
                        before returned.
        :return: a :class:`list`
        """
        if key not in self:
            default_list = list(default_list or ())
            dict.__setitem__(self, key, default_list)
        else:
            default_list = dict.__getitem__(self, key)
        return default_list

    def items(self, multi=False):
        """Return an iterator of ``(key, value)`` pairs.

        :param multi: If set to `True` the iterator returned will have a pair
                      for each value of each key.  Otherwise it will only
                      contain pairs for the first value of each key.
        """

        for key, values in iteritems(dict, self):
            if multi:
                for value in values:
                    yield key, value
            else:
                yield key, values[0]

    def lists(self):
        """Return a list of ``(key, values)`` pairs, where values is the list
        of all values associated with the key."""

        for key, values in iteritems(dict, self):
            yield key, list(values)

    def keys(self):
        return iterkeys(dict, self)

    __iter__ = keys

    def values(self):
        """Returns an iterator of the first value on every key's value list."""
        for values in itervalues(dict, self):
            yield values[0]

    def listvalues(self):
        """Return an iterator of all values associated with a key.  Zipping
        :meth:`keys` and this is the same as calling :meth:`lists`:

        >>> d = MultiDict({"foo": [1, 2, 3]})
        >>> zip(d.keys(), d.listvalues()) == d.lists()
        True
        """
        return itervalues(dict, self)

    def copy(self):
        """Return a shallow copy of this object."""
        return self.__class__(self)

    def deepcopy(self, memo=None):
        """Return a deep copy of this object."""
        return self.__class__(deepcopy(self.to_dict(flat=False), memo))

    def to_dict(self, flat=True):
        """Return the contents as regular dict.  If `flat` is `True` the
        returned dict will only have the first item present, if `flat` is
        `False` all values will be returned as lists.

        :param flat: If set to `False` the dict returned will have lists
                     with all the values in it.  Otherwise it will only
                     contain the first value for each key.
        :return: a :class:`dict`
        """
        if flat:
            return dict(iteritems(self))
        return dict(self.lists())

    def update(self, other_dict):
        """update() extends rather than replaces existing key lists."""
        for key, value in iter_multi_items(other_dict):
            MultiDict.add(self, key, value)

    def pop(self, key, default=_missing):
        """Pop the first item for a list on the dict.  Afterwards the
        key is removed from the dict, so additional values are discarded:

        >>> d = MultiDict({"foo": [1, 2, 3]})
        >>> d.pop("foo")
        1
        >>> "foo" in d
        False

        :param key: the key to pop.
        :param default: if provided the value to return if the key was
                        not in the dictionary.
        """
        try:
            return dict.pop(self, key)[0]
        except KeyError as e:
            if default is not _missing:
                return default
            raise

    def popitem(self):
        """Pop an item from the dict."""
        item = dict.popitem(self)
        return (item[0], item[1][0])

    def poplist(self, key):
        """Pop the list for a key from the dict.  If the key is not in the dict
        an empty list is returned.
        """
        return dict.pop(self, key, [])

    def popitemlist(self):
        """Pop a `(key, list)` tuple from the dict."""
        return dict.popitem(self)

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        return self.deepcopy(memo=memo)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, list(iteritems(self, multi=True)))
