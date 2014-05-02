import sys

PY2 = sys.version_info[0] == 2

if PY2:
    iterkeys = lambda d, *args, **kwargs: d.iterkeys(*args, **kwargs)
    itervalues = lambda d, *args, **kwargs: d.itervalues(*args, **kwargs)
    iteritems = lambda d, *args, **kwargs: d.iteritems(*args, **kwargs)
    iterlists = lambda d, *args, **kwargs: d.iterlists(*args, **kwargs)

else:
    iterkeys = lambda d, *args, **kwargs: iter(d.keys(*args, **kwargs))
    itervalues = lambda d, *args, **kwargs: iter(d.values(*args, **kwargs))
    iteritems = lambda d, *args, **kwargs: iter(d.items(*args, **kwargs))
    iterlists = lambda d, *args, **kwargs: iter(d.lists(*args, **kwargs))


def iter_multi_items(mapping):
    """Iterates over the items of a mapping yielding keys and values
    without dropping any from more complex structures.
    """
    if isinstance(mapping, MultiDict):
        for item in iteritems(mapping, multi=True):
            yield item
    elif isinstance(mapping, dict):
        for key, value in iteritems(mapping):
            if isinstance(value, (tuple, list)):
                for value in value:
                    yield key, value
            else:
                yield key, value
    else:
        for item in mapping:
            yield item


def native_itermethods(names):
    if not PY2:
        return lambda x: x
    def setmethod(cls, name):
        itermethod = getattr(cls, name)
        setattr(cls, 'iter%s' % name, itermethod)
        listmethod = lambda self, *a, **kw: list(itermethod(self, *a, **kw))
        listmethod.__doc__ = 'Like `iter%s`, but returns a list.' % name
        setattr(cls, name, listmethod)

    def wrap(cls):
        for name in names:
            setmethod(cls, name)
        return cls
    return wrap
