""" js2esi.node.util
Module to help with generating logical constructs.
"""

import io

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


def glob2re(glob):
    # tbd: any other chars need replacing?... perhaps use re.quote()?...
    return '^' + glob.replace('+', '\\+').replace('.', '\\.').replace('*', '.*').replace('?', '.') + '$'


def assertOnlyKeywords(dictobj, *keys):
    if len(set(dictobj.keys()) - set(['debug'])) > 0:
        raise TypeError('unexpected keywords: "%s"' % ('", "'.join(set(dictobj.keys()) - set(['debug'])),))


def expr(obj):
    from js2esi.node.expression import Expression
    from js2esi.node.literal import Literal
    if obj is None:
        return None
    if isinstance(obj, Expression):
        return obj
    return Literal(obj)


class ContextIndent:
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

#
# # TODO: do this more elegantly...
# def getContext():
#   import js2esi.node
#   return js2esi.node.context

# def isDebug():
#   return getContext().debug
