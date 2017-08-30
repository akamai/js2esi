""" js2esi.token.adict
At its core, an ``adict`` is just an automatic-attribute version of
dict(), i.e. all items are automatically converted to
attributes. However, ``adict`` also adds the ability to inherit
attributes from other adicts or objects.

TODO: is this *REALLY* the right thing to do??? (ie. is there no
standard class that provides automatic object attribute access???)

TODO: the adict() constructor does not follow the same constructor pattern as
dict() --- that should be fixed.

TODO: one problem with the auto_adict is that it breaks if the value
          is an array of dicts...
TODO: it would be interesting to have a 'no-inherit' list of attributes...
"""

import types

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


def adict2dict(o):
    if isinstance(o, str ):
        return o
    try:
        # try it as a dict-like object...
        return dict([(adict2dict(k), adict2dict(v)) for k, v in o.items()])
    except AttributeError:
        pass
    try:
        # try it as a list-like object...
        return [adict2dict(e) for e in o]
    except TypeError:
        pass
    return o


class adict(object):
    def new(**kwargs):
        return adict().update(kwargs)

    new = staticmethod(new)

    def enhance(obj):
        if hasattr(obj, 'keys') and hasattr(obj, 'items'):
            return adict().update(obj)
        if isinstance(obj, str): return obj
        try:
            return [adict.enhance(e) for e in obj]
        except TypeError:
            return obj

    enhance = staticmethod(enhance)

    def __init__(self, inherit=None, auto_adict=True):
        # TODO: should inherit be auto-converted as well?
        self.__dict__['inherit'] = inherit
        self.__dict__['values'] = {}
        self.__dict__['auto-adict'] = auto_adict

    def __setattr__(self, key, val):
        return self.set(key, val)

    def __getattr__(self, key):
        return self.get(key)

    def __delattr__(self, key):
        return self.rem(key)

    def __setitem__(self, key, val):
        return self.set(key, val)

    def __getitem__(self, key):
        return self.get(key)

    def __delitem__(self, key):
        return self.rem(key)

    def toDict(self):
        return adict2dict(self)

    def update(self, new_values):
        for k, v in new_values.items(): self.set(k, v)
        return self

    def get(self, key, default=None, inherit=True):
        ret = self.__dict__['values'].get(key, None)
        if ret is not None: return ret
        if inherit and self.__dict__['inherit'] is not None:
            return self.inherit.get(key, default, inherit)
        return default

    def set(self, key, val):
        if self.__dict__['auto-adict']:
            def convDict(val):
                if type(val) in [dict]:
                    return adict().update(val)
                return val

            if type(val) in [list, slice, tuple]:
                val = [convDict(v) for v in val]
            else:
                val = convDict(val)
        self.__dict__['values'][key] = val
        return self

    def rem(self, key, inherit=False):
        # TODO: in the case of inherit = False, this may not accomplish the
        #      desired behavior, possible solutions:
        #        - store None, eg: self.__dict__[key] = None
        #        - store a list of deleted attributes (ugh)
        del self.__dict__[key]
        if inherit and self.__dict__['inherit'] is not None:
            self.inherit.rem(key, inherit)
        return self

    # TODO: need to copy all dictionary methods...
    #   __class__,
    #   __doc__, , __getattribute__, __ge__,
    #   __hash__, __init__, __iter__, __le__, __ne__,
    #   __new__, __reduce__, __reduce_ex__,
    #   clear, copy, fromkeys, iteritems, iterkeys, itervalues,
    #   pop, popitem, setdefault']
    # DONE:
    #   get, has_key, items, keys, update, values, __[set|get|del]attr__
    #   __repr__, __str__, __cmp__, __lt__, __gt__, __eq__, __[set|get|del]item__,
    #   __len__, __contains__
    def keys(self, inherit=True):
        if inherit and self.__dict__['inherit'] is not None:
            return set(self.__dict__['values'].keys() + self.__dict__['inherit'].keys())
        return self.__dict__['values'].keys()

    def values(self, inherit=True):
        return [self.get(key) for key in self.keys(inherit)]

    def items(self, inherit=True):
        return [(key, self.get(key)) for key in self.keys(inherit)]

    def has_key(self, key, inherit=True):
        if self.__dict__['values'].has_key(key): return True
        if inherit and self.__dict__['inherit'] is not None:
            return self.__dict__['inherit'].has_key(key)
        return False

    def __contains__(self, key):
        return self.has_key(key)

    def __len__(self, inherit=True):
        return len(self.keys(inherit))

    def __repr__(self):
        if self.__dict__['inherit'] is None:
            return '<%s %r>' % (type(self).__name__, self.__dict__['values'])
        return '<%s %r, inheriting-from: %r>' \
               % (type(self).__name__, self.__dict__['values'], self.__dict__['inherit'])

    def __str__(self):
        return str(dict(self.items()))

    # TODO: some of these should invoke the parent adict as well...
    def __cmp__(self, other):
        if hasattr(other, '__dict__'):
            return cmp(self.__dict__['values'], other.__dict__['values'])
        return cmp(self.__dict__['values'], dict())

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0
