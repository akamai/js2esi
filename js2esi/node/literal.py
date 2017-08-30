""" js2esi.node.literal
logical literal object (string, number, etc) abstraction
"""

import re, types
from js2esi.node.expression import Expression

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class InvalidNegation(Exception): pass


class Literal(Expression):
    def __init__(self, value=None):
        super(Literal, self).__init__()
        self.value = value

    @property
    def __label__(self):
        return '%s(%r)' % (super(Literal, self).__label__, self.value)

    @property
    def type(self):
        if isinstance(self.value, bool):
            return 'boolean'
        if isinstance(self.value, int) or isinstance(self.value, float):
            return 'number'
        if isinstance(self.value, str):
            return 'string'
        raise TypeError('unknown literal value type "%s"' % (type(self.value),))

    def __neg__(self):
        if self.type == 'number':
            return Literal(- self.value)
        raise InvalidNegation()

    def __js__(self, ctxt):
        # tbd: any other types that this should be sensitive to?...
        if self.type == 'boolean':
            return ctxt.write(self.value and 'true' or 'false')
        if self.type == 'number':
            return ctxt.write(str(self.value))
        # tbd: this is the quick-and-dirty solution, but it probably beats *everything*
        #      mostly because it does non-printable-character escaping so beautifully!...
        ctxt.write(repr(str(self.value)))

    def __esi__(self, ctxt):
        # tbd: any other types that this should be sensitive to?...
        if self.type == 'boolean':
            return ctxt.write(self.value and '1' or '0')
        if self.type == 'number':
            return ctxt.write(str(self.value))
        if ctxt.isvars:
            return ctxt.write(re.sub(r'([$\\]|<esi:)', r'\\\1', str(self.value)))
        ctxt.write('\'')
        ctxt.write(str(self.value).replace('\\', '\\\\').replace('\'', '\\\''))
        ctxt.write('\'')
