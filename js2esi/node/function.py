""" js2esi.node.literal
logical function definition abstraction
"""
import copy
from js2esi.node.base import StructureError
from js2esi.node.statement import Statement, Block
from js2esi.node.variable import Variable, Assign
from js2esi.node.expression import FunctionCall, Operator
from js2esi.node.literal import Literal
from js2esi.node import util

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class FunctionDefinition(Statement):
    def __init__(self, name, params, executionBlock, inline=False):
        super(FunctionDefinition, self).__init__()
        # tbd: validate function name?...
        self.name = name
        self.params = params
        self.expr = executionBlock
        self.inline = inline

    @property
    def __label__(self):
        return '%s%s(%s)' % (self.inline and "inline " or "", super(FunctionDefinition, self).__label__, self.name)

    def __esi__(self, ctxt):
        if self.inline:
            return
        ctxt.write('<esi:function name="%s">' % self.name)
        for idx, p in enumerate(self.params):
            ctxt.paramIndex = idx
            p.esi(ctxt)
        self.expr.esi(ctxt)
        ctxt.write('</esi:function>')

    def inlineInto(self, caller):
        # many restrictions...
        #   - inline function can comprise a single return statement only
        #   - arg and param count must match up, or params must have defaults
        #   - inline function cannot reference ARGS variable
        #   - function args can only be literals, simple variables, and function calls
        # tbd: the ARGS restriction is really a bit excessive, but c'mon...
        # tbd: should be invoked only in general expression context - once i
        #      support more powerful inlining...
        # tbd: i should keep a stack of inlining functions... to catch recursive calls
        expr = self.expr
        while isinstance(expr, Block) and len(expr.statements) == 1:
            expr = expr.statements[0]
        if isinstance(expr, FunctionReturn):
            expr = expr.expr
        else:
            raise StructureError('inlined function %s() body can currently only comprise a single return statement'
                                 % (self.name,))
        if not isinstance(caller, FunctionCall):
            raise StructureError('inlined function %s() can only by called by a FunctionCall, not "%s"'
                                 % (self.name, caller.__class__.__name__,))
        if len(caller.args) > len(self.params):
            raise StructureError('inline function %s() takes at most %d argument%s (%d given)'
                                 % (self.name, len(self.params),
                                    len(self.params) != 1 and 's' or '',
                                    len(caller.args)))
        if len(caller.args) != len(self.params):
            for idx in range(len(caller.args), len(self.params)):
                if self.params[idx].default is not None:
                    continue
                raise StructureError('call to inline function %s() does not provide a value'
                                     ' for parameter "%s" (at index %d)'
                                     % (self.name, self.params[idx].name, idx))
        for arg in caller.args:
            if isinstance(arg, Literal):
                continue
            if isinstance(arg, FunctionCall):
                continue
            if not isinstance(arg, Variable):
                raise StructureError('inline function %s() called with type "%s"'
                                     ' (currently, only literals, simple variables'
                                     ' or function calls are allowed)'
                                     % (self.name, arg.__class__.__name__))
            if arg.key is not None or arg.default is not None:
                raise StructureError('inline function %s() called with non-simple variable'
                                     ' (i.e. with a subkey or a default)'
                                     % (self.name,))

        expr = copy.deepcopy(expr)
        vartab = dict()
        for idx in range(len(caller.args)):
            vartab[self.params[idx].name] = caller.args[idx]
        for idx in range(len(caller.args), len(self.params)):
            vartab[self.params[idx].name] = self.params[idx].default
        proxies = []
        for var in util.allchildren(expr):
            if not isinstance(var, Variable):
                continue
            if var.name == 'ARGS':
                raise StructureError('inline function %s() cannot use variable "ARGS"'
                                     % (self.name,))
            if var.name not in vartab:
                continue
            proxies.append(var)
        for var in proxies:
            var._proxy = copy.deepcopy(vartab[var.name])
        caller._proxy = expr
        return self

    def __js__(self, ctxt):
        ctxt.write(ctxt.indent + 'function %s(' % (self.name,))
        for idx, p in enumerate(self.params):
            if idx != 0:
                ctxt.write(', ')
            p.js(ctxt)
        ctxt.write(')\n')
        ctxt.indent += 1
        self.expr.js(ctxt)
        ctxt.indent -= 1
        # tbd: perhaps i should force a block if self.expr is not a Block?...
        # ctxt.write(')\n%s{\n' % (ctxt.indent,))
        # ctxt.indent += 1
        # self.expr.js(ctxt)
        # ctxt.indent -= 1
        # ctxt.write(ctxt.indent + '}\n')


FunctionDef = FunctionDefinition
FuncDef = FunctionDefinition


class FunctionParam(Statement):
    def __init__(self, name, default=None):
        super(FunctionParam, self).__init__()
        self.name = name
        self.default = default

    def __esi__(self, ctxt):
        # TODO: now that i have Variable._proxy, i should inspect the function
        #      body to see if i need to create a temporary variable, or use it
        #      directly. eg:
        #        def func(a, b)
        #          return a * b['key'];
        #      should result in:
        #        <esi:function name="func">
        #          <esi:assign name="b" value="$(ARGS{1})"/>
        #          <esi:return value="$(ARGS{0})*$(b{'key'})"/>
        #        </esi:function>
        Assign(self.name,
               Variable('ARGS', key=ctxt.paramIndex, default=self.default)).esi(ctxt)
        # tbd: what about __js__?... since ESI does not support function params,
        #      this will never be called during decomp. however, it could be called
        #      when doing js => node => js, or during node programmatic generation...


class FunctionReturn(Statement):
    def __init__(self, expr):
        super(FunctionReturn, self).__init__()
        self.expr = expr

    def __esi__(self, ctxt):
        if self.expr is None:
            ctxt.write('<esi:return/>')
            return
        ctxt.write('<esi:return value="')
        # tbd: escape return value?...
        self.expr.esi(ctxt)
        ctxt.write('"/>')

    def __js__(self, ctxt):
        if self.expr is None:
            ctxt.write('%sreturn;\n' % (ctxt.indent,))
        ctxt.write('%sreturn ' % (ctxt.indent,))
        self.expr.js(ctxt)
        ctxt.write(';\n')
