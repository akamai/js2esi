""" js2esi.node.util
Module to help with generating logical constructs.
"""
import io

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


def glob2re(glob):
    # TODO: any other chars need replacing?... perhaps use re.quote()?...
    return '^' + glob.replace('+', '\\+').replace('.', '\\.').replace('*', '.*').replace('?', '.') + '$'


def assertOnlyKeywords(dictobj, *keys):
    if len(set(dictobj.keys()) - set(keys)) > 0:
        raise TypeError('unexpected keywords: "%s"' % ('", "'.join(set(dictobj.keys()) - set(keys)),))


def expr(obj):
    from js2esi.node.expression import Expression
    from js2esi.node.literal import Literal
    if obj is None:
        return None
    if isinstance(obj, Expression):
        return obj
    return Literal(obj)


class ContextIndent(object):
    def __init__(self):
        self.i = 0

    def __int__(self):
        return self.i

    def __add__(self, v):
        if isinstance(v, int) or isinstance(v, float):
            return int(self) + v
        return str(self) + str(v)

    def __iadd__(self, v):
        self.i += v
        return self

    def __isub__(self, v):
        self.i -= v
        return self

    def __str__(self):
        return self.i * '  '


class Context(object):
    def __init__(self):
        self.debug = False
        self.matchname = None
        self.testlevel = 0
        self.isvars = False
        self.indent = ContextIndent()
        self.buffers = []
        self.out = None
        self.lib = []
        self.inlines = {}

    def write(self, msg):
        self.out.write(msg)

    def push_buffered(self):
        self.buffers.append(self.out)
        self.out = io.StringIO()

    def pop_buffered(self):
        ret = self.out.getvalue()
        self.out = self.buffers.pop()
        return ret

    def save_buffered(self):
        self.out.write(self.pop_buffered())


def allchildren(item, kls=None, test=None):
    for sub in item.children:
        if (kls is None or isinstance(sub, kls)) and (test is None or test(sub)):
            yield sub
        for i in allchildren(sub, kls=kls, test=test):
            yield i
