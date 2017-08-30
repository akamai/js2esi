""" js2esi.node.expr
logical expressions abstraction
TODO: i should be able to simplify all the "Operator._registry['...'] = ..."
      as a metaclass execution...
"""

from js2esi.node.base import Item
from js2esi.node import util

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class MatchNameConflict(Exception): pass


class BadMatchNameContext(Exception): pass


class OperatorError(Exception): pass


class UnknownOperator(Exception): pass


class Expression(Item): pass


Expr = Expression


class FunctionCall(Expression):
    def __init__(self, name, *argExprs, **kwargs):
        super(FunctionCall, self).__init__()
        util.assertOnlyKeywords(kwargs, 'debug')
        self.name = name
        self.args = argExprs
        self.debug = kwargs.get('debug', 'translate')

    @property
    def __label__(self):
        return '%s(%s)' % (super(FunctionCall, self).__label__, self.name)

    def __esi__(self, ctxt):
        from js2esi.node.literal import Literal
        if ctxt.debug:
            if self.debug is None:
                return
            if self.debug == 'translate':
                # TODO: generalize this...
                if self.name == 'add_header':
                    from js2esi.node.log import Log
                    Log.d('adding response header "',
                          self.args[0], '" to: ', self.args[1]).esi(ctxt)
                    return
        # if self.name in ctxt.inlines:
        #   return ctxt.inlines[self.name].inlineEsi(ctxt, self)
        ctxt.write('$' + self.name + '(')
        for idx, arg in enumerate(self.args):
            if idx != 0:
                ctxt.write(',')
            arg.esi(ctxt)
        ctxt.write(')')

    def __js__(self, ctxt):
        ctxt.write(self.name + '(')
        for idx, arg in enumerate(self.args):
            if idx != 0:
                ctxt.write(', ')
            arg.js(ctxt)
        ctxt.write(')')


Function = FunctionCall
Func = FunctionCall


class Operator(Expression):
    _registry = dict()

    @staticmethod
    def getClassForOperator(operator):
        try:
            return Operator._registry[operator]
        except KeyError:
            raise UnknownOperator(operator)

    def __init__(self, operator, *args):
        super(Operator, self).__init__()
        self.op = operator
        self.args = []
        for arg in args:
            self.append(arg)

    @property
    def __label__(self):
        return '%s(%s)' % (super(Operator, self).__label__, self.op)

    def append(self, expr):
        if expr is None:
            return
        self.args.append(expr)

    def getArgs(self):
        return self.args

    def __esi__(self, ctxt):
        args = self.getArgs()
        if len(args) <= 0:
            return
        if len(args) == 1:
            return args[0].esi(ctxt)
        for idx, arg in enumerate(args):
            if idx != 0:
                ctxt.write(self.op)
            if isinstance(arg, Operator) and not ctxt.isvars:
                ctxt.write('(')
                arg.esi(ctxt, isvars=ctxt.isvars)
                ctxt.write(')')
            else:
                arg.esi(ctxt, isvars=ctxt.isvars)

    def __js__(self, ctxt):
        args = self.getArgs()
        if len(args) <= 0:
            return
        if len(args) == 1:
            return args[0].js(ctxt)
        for idx, arg in enumerate(args):
            if idx != 0:
                ctxt.write(' %s ' % self.op)
            if isinstance(arg, Operator):
                ctxt.write('(')
                arg.js(ctxt)
                ctxt.write(')')
            else:
                arg.js(ctxt)


Op = Operator


class UnaryOperator(Operator):
    def __init__(self, operator, expr):
        Operator.__init__(self, operator, expr)

    def __esi__(self, ctxt):
        if len(self.getArgs()) != 1:
            raise OperatorError('unary %s operator takes exactly one argument' % (self.__class__.__name__,))
        expr = self.getArgs()[0]
        if isinstance(expr, Operator):
            ctxt.write('%s(' % (self.op,))
            expr.esi(ctxt)
            ctxt.write(')')
            return
        ctxt.write(self.op)
        expr.esi(ctxt)

    def __js__(self, ctxt):
        if len(self.getArgs()) != 1:
            raise OperatorError('unary %s operator takes exactly one argument' % (self.__class__.__name__,))
        expr = self.getArgs()[0]
        if isinstance(expr, Operator):
            ctxt.write('%s (' % (self.op,))
            expr.js(ctxt)
            ctxt.write(')')
            return
        ctxt.write('%s ' % (self.op,))
        expr.js(ctxt)


class Not(UnaryOperator):
    def __init__(self, expr):
        UnaryOperator.__init__(self, '!', expr)


Operator._registry['!'] = Not


class And(Operator):
    def __init__(self, *args):
        Operator.__init__(self, '&&', *args)

    def getArgs(self):
        return [e for e in Operator.getArgs(self) if str(e) != '1']

    def __esi__(self, ctxt):
        # do an optimization to determine if any operands resolve to false
        for arg in self.args:
            ctxt.push_buffered()
            arg.esi(ctxt)
            tmp = ctxt.out.getvalue()
            ctxt.pop_buffered()
            if tmp == '0':
                return ctxt.write('0')
        return Operator.__esi__(self, ctxt)


Operator._registry['&&'] = And


class Or(Operator):
    def __init__(self, *args):
        Operator.__init__(self, '||', *args)

    def getArgs(self):
        return [e for e in Operator.getArgs(self) if str(e) != '0']

    def __esi__(self, ctxt):
        # do an optimization to determine if any operands resolve to true
        for arg in self.args:
            ctxt.push_buffered()
            arg.esi(ctxt)
            tmp = ctxt.out.getvalue()
            ctxt.pop_buffered()
            if tmp == '1':
                return ctxt.write('1')
        return Operator.__esi__(self, ctxt)


Operator._registry['||'] = Or


class Equal(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '==', leftExpr, rightExpr)


Operator._registry['==='] = Equal
Operator._registry['=='] = Equal
Eq = Equal


class NotEqual(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '!=', leftExpr, rightExpr)


Operator._registry['!=='] = NotEqual
Operator._registry['!='] = NotEqual
Ne = NotEqual


class LesserThan(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '<', leftExpr, rightExpr)


Operator._registry['<'] = LesserThan
Lt = LesserThan


class LesserEqual(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '<=', leftExpr, rightExpr)


Operator._registry['<='] = LesserEqual
Le = LesserEqual


class GreaterThan(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '>', leftExpr, rightExpr)


Operator._registry['>'] = GreaterThan
Gt = GreaterThan


class GreaterEqual(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '>=', leftExpr, rightExpr)


Operator._registry['>='] = GreaterEqual
Ge = GreaterEqual


# TODO: consecutive Literals of the same kind can be collapsed...
#      => this is somewhat being handled by token/cparser.py.
class Add(Operator):
    def __init__(self, *argExprs):
        Operator.__init__(self, '+', *argExprs)

    def __esi__(self, ctxt):
        if ctxt.isvars:
            return Operator('', *self.args).__esi__(ctxt)
        return Operator.__esi__(self, ctxt)


Operator._registry['+'] = Add
Plus = Add


class Subtract(Operator):
    def __init__(self, *argExprs):
        Operator.__init__(self, '-', *argExprs)


Operator._registry['-'] = Subtract
Minus = Subtract


class Multiply(Operator):
    def __init__(self, *argExprs):
        Operator.__init__(self, '*', *argExprs)


Operator._registry['*'] = Multiply
Times = Multiply


class Modulus(Operator):
    def __init__(self, *argExprs):
        Operator.__init__(self, '%', *argExprs)


Operator._registry['%'] = Modulus
Mod = Modulus


class Divide(Operator):
    def __init__(self, *argExprs):
        Operator.__init__(self, '/', *argExprs)


Operator._registry['/'] = Divide


class Matches(Operator):
    def __init__(self, leftExpr, rightExpr, matchName=None, case=True):
        Operator.__init__(self, case and ' matches ' or ' matches_i ', leftExpr, rightExpr)
        self.matchName = matchName

    @property
    def __label__(self):
        return '%s' % (self.__class__.__name__,)

    def __esi__(self, ctxt):
        # ret = Operator.__str__(self)
        # ctxt = util.getContext()
        if ctxt.matchname is not None:
            raise MatchNameConflict('pre-existing match name detected ("%s"), conflicts with new "%s"'
                                    % (ctxt.matchname, self.matchName or '(default)'))
        if self.matchName is None:
            return Operator.__esi__(self, ctxt)
        if ctxt.testlevel <= 0:
            raise BadMatchNameContext()
        ctxt.matchname = self.matchName
        return Operator.__esi__(self, ctxt)

    def __js__(self, ctxt):
        # in token, we already surround operators with a space, so we can remove them
        # here.
        # TODO: this should really be done in reverse - ie. __esi__ should inject the
        #      spaces instead.
        Operator(self.op.strip(), *self.args).__js__(ctxt)
        if self.matchName is not None:
            ctxt.write(' as %s' % (self.matchName,))


Operator._registry['matches'] = Matches


class MatchesNoCase(Matches):
    def __init__(self, leftExpr, rightExpr, matchName=None):
        Matches.__init__(self, leftExpr, rightExpr, matchName=matchName, case=False)


Operator._registry['matches_i'] = MatchesNoCase


class Has(Operator):
    def __init__(self, leftExpr, rightExpr, case=True):
        Operator.__init__(self, case and ' has ' or ' has_i ', leftExpr, rightExpr)

    @property
    def __label__(self):
        return '%s' % (self.__class__.__name__,)

    def __js__(self, ctxt):
        # in js, we already surround operators with a space, so we can remove them
        # here.
        # TODO: this should really be done in reverse - ie. __esi__ should inject the
        #      spaces instead.
        Operator(self.op.strip(), *self.args).__js__(ctxt)


Operator._registry['has'] = Has


class HasNoCase(Has):
    def __init__(self, leftExpr, rightExpr):
        Has.__init__(self, leftExpr, rightExpr, case=False)


Operator._registry['has_i'] = HasNoCase


class BitShiftLeft(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '<<', leftExpr, rightExpr)


Operator._registry['<<'] = BitShiftLeft


class BitShiftRight(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '>>', leftExpr, rightExpr)


Operator._registry['>>'] = BitShiftRight


class BitwiseNot(UnaryOperator):
    def __init__(self, expr):
        UnaryOperator.__init__(self, '~', expr)


Operator._registry['~'] = BitwiseNot


class BitwiseAnd(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '&', leftExpr, rightExpr)


Operator._registry['&'] = BitwiseAnd


class BitwiseOr(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '|', leftExpr, rightExpr)


Operator._registry['|'] = BitwiseOr


class BitwiseXor(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '^', leftExpr, rightExpr)


Operator._registry['^'] = BitwiseXor


class Range(Operator):
    def __init__(self, leftExpr, rightExpr):
        Operator.__init__(self, '..', leftExpr, rightExpr)


Operator._registry['..'] = Range