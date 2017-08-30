""" js2esi.node.variable
logical variable abstraction
"""

from js2esi.node.statement import Statement, Block
from js2esi.node.expression import Expression, Function, Plus
from js2esi.node.literal import Literal
from js2esi.node.variable import Assign, Var

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class Debug(Statement):
    def __init__(self, *expressions, **kwargs):
        super(Debug, self).__init__()
        self.expr = Plus()
        for e in expressions:
            if not isinstance(e, Expression):
                e = Literal(e)
            self.expr.append(e)
        if kwargs.get('nl', True):
            self.expr.append(Literal('\n'))

    def __esi__(self, ctxt):
        if not ctxt.debug:
            return
        # tbd: note that this makes the assumption that everything is very
        #      linear in the ESI... perhaps use a function call?...
        Assign('node_debug', Plus(Var('node_debug'), self.expr)).esi(ctxt)


class DebugBlock(Block):
    def __init__(self):
        super(DebugBlock, self).__init__()
        self.init = Block(Assign('node_debug', ''), Assign('node_indent', ''))
        self.term = Function('set_response_code', Literal(444), Var('node_debug'))

    def __esi__(self, ctxt):
        if not ctxt.debug:
            return Block.__esi__(self, ctxt)
        self.init.esi(ctxt)
        Block.__esi__(self, ctxt)
        self.term.esi(ctxt)


class IfDebug(Block):
    def __esi__(self, ctxt):
        if ctxt.debug:
            Block.__esi__(self, ctxt)


class Log(object):
    @staticmethod
    def indent():
        return IfDebug(Assign('node_indent', Plus(Var('node_indent'), Literal('  '))))

    @staticmethod
    def outdent():
        return IfDebug(Assign('node_indent', Function('substr', Var('node_indent'), Literal(0), Literal(-2))))

    @staticmethod
    def d(*expressions, **kwargs):
        return Debug('[  ] ', Var('node_indent'), *expressions, **kwargs)
