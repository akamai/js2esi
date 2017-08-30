""" js2esi.node.variable
logical variable abstraction
"""

from js2esi.node.statement import Statement
from js2esi.node.expression import Expression, Operator
from js2esi.node import util, StructureError

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class Variable(Expression):
    def __init__(self, name, key=None, default=None):
        super(Variable, self).__init__()

        self.name = name
        self.key = util.expr(key)
        self.default = util.expr(default)
        if isinstance(name, Variable):
            self.name = name.name
            if key is not None and name.key is not None:
                raise StructureError("A variable defined in a variable - should shouldn't have happened!")
            elif name.key is not None:
                self.key = name.key

            if default is not None and name.default is not None:
                raise StructureError("A variable defined in a variable - should shouldn't have happened!")
            elif name.default is not None:
                self.default = name.default

    @property
    def __label__(self):
        return '%s(%s)' % (super(Variable, self).__label__, self.name)

    def __esi__(self, ctxt):
        ctxt.write('$(%s' % (self.name,))
        if self.key is not None:
            ctxt.write('{')
            self.key.esi(ctxt)
            ctxt.write('}')
        if self.default is not None:
            ctxt.write('|')
            self.default.esi(ctxt)
        ctxt.write(')')

    def __js__(self, ctxt):
        ctxt.write(self.name)
        if self.key is not None:
            ctxt.write('[')
            self.key.js(ctxt)
            ctxt.write(']')
        if self.default is not None:
            ctxt.write('||')
            self.default.js(ctxt)


Var = Variable


class Assign(Statement):
    def __init__(self, name, valueExpr, key=None):
        super(Assign, self).__init__()
        self.name = name
        self.key = util.expr(key)
        self.value = util.expr(valueExpr)

    @property
    def __label__(self):
        return '%s(%s)' % (super(Assign, self).__label__, self.name)

    def __esi__(self, ctxt):
        # tbd: perhaps the double-quote can be escaped somehow?...
        ctxt.write('<esi:assign name="')
        ctxt.write(self.name)
        if self.key is not None:
            ctxt.write('{')
            self.key.esi(ctxt)
            ctxt.write('}')
        ctxt.write('"')
        val = self.value.esibuf(ctxt)
        if '\n' in val or '"' in val:
            return ctxt.write('>%s</esi:assign>' % val)
        return ctxt.write(' value="%s"/>' % val)

    def __js__(self, ctxt):
        ctxt.write(str(ctxt.indent))
        name = self.name
        if self.key is not None:
            name = '%s[%s]' % (name, self.key.jsbuf(ctxt))
        ctxt.write(name)
        ctxt.write((getattr(ctxt, 'assignwidth', 0) - len(name)) * ' ')
        # converting "a = a + X" to "a += X" and any other operator that supports
        # that form of associative assignment (is that the right term??)...
        # tbd: is this really the right way?... should i be creating a class
        #      "AssociativeAssign"?...
        if isinstance(self.value, Operator) \
                and self.value.op in ['+', '-', '*', '%', '/'] \
                and isinstance(self.value.args[0], Variable) \
                and self.value.args[0].name == self.name \
                and self.value.args[0].key == self.key:
            ctxt.write(' %s= ' % (self.value.op,))
            Operator(self.value.op, *self.value.args[1:]).js(ctxt)
        else:
            ctxt.write(' = ')
            self.value.js(ctxt)
        ctxt.write(';\n')

    def width(self, ctxt):
        ret = len(self.name)
        if self.key is not None:
            ret += 2 + len(self.key.jsbuf(ctxt))
        return ret
