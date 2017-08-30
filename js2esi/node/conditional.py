""" js2esi.node.conditional
logical conditionals abstraction
"""
from js2esi.node.statement import Statement, Block
from js2esi.node.expression import Operator, Not
from js2esi.node.log import Debug

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class DanglingMatchName(Exception): pass


def findMatchOperator(expr):
    # TODO: determine the "correct" way to find the "matches" or "matches_i"
    #      operator that applies to the matchname...
    #      this algorithm is doing a first-hit deep-first search...
    # TODO: this needs to be refactored... use the Item.children property?...
    if isinstance(expr, Not):
        return findMatchOperator(expr.expr)
    if not isinstance(expr, Operator):
        return None
    if expr.op in [' matches ', ' matches_i ']:
        return expr
    for op in expr.args:
        ret = findMatchOperator(op)
        if ret is not None:
            return ret
    return None


class If(Statement):
    def __init__(self, testExpr, matchStatement, noMatchStatement=None, debug=None):
        super(If, self).__init__()
        if debug is not None:
            # TODO: this debugging breaks the if/else if/else detection to create a
            #      single choose/when/when!...
            try:
                if len(debug) != 3:
                    debug = [debug, Debug('yes'), Debug('no')]
            except (TypeError, AttributeError):
                debug = [debug, Debug('yes'), Debug('no')]
            matchStatement = Block(debug[1], matchStatement)
            noMatchStatement = Block(debug[2], noMatchStatement)
        self.test = testExpr
        self.match = matchStatement
        self.nomatch = noMatchStatement
        self.debug = debug is not None and debug[0] or None

    def setMatchName(self, matchname):
        me = findMatchOperator(self.test)
        if me is None:
            raise DanglingMatchName(matchname)
        me.matchName = matchname

    def __esi__(self, ctxt):
        if ctxt.testlevel > 0:
            ctxt.write('<esi:when test="')
            self.test.esi(ctxt)
            ctxt.write('"')
            if ctxt.matchname is not None:
                ctxt.write(' matchname="%s"' % ctxt.matchname)
                ctxt.matchname = None
            ctxt.write('>')
            if self.match is not None:
                tl = ctxt.testlevel
                ctxt.testlevel = 0
                self.match.esi(ctxt)
                ctxt.testlevel = tl
            ctxt.write('</esi:when>')
            if self.nomatch is None:
                return
            if isinstance(self.nomatch, If):
                self.nomatch.esi(ctxt)
            else:
                ctxt.push_buffered()
                tl = ctxt.testlevel
                ctxt.testlevel = 0
                self.nomatch.esi(ctxt)
                ctxt.testlevel = tl
                val = ctxt.pop_buffered()
                if len(val) > 0:
                    ctxt.write('<esi:otherwise>')
                    ctxt.write(val)
                    ctxt.write('</esi:otherwise>')
            return
        if self.debug is not None:
            self.debug.esi(ctxt)
        ctxt.write('<esi:choose>')
        ctxt.testlevel = 1
        self.__esi__(ctxt)
        ctxt.testlevel = 0
        ctxt.write('</esi:choose>')

    def __js__(self, ctxt):
        priortestlevel = ctxt.testlevel
        ctxt.write(ctxt.indent + (ctxt.testlevel <= 0 and 'if' or 'else if') + ' ( ')
        self.test.js(ctxt)
        ctxt.write(' )\n')
        if self.match is not None:
            ctxt.indent += 1
            # putting an explicit Block around an If in order to force braces around
            # them. technically, i only need to put braces around the If IFF it does
            # NOT also have a nomatch clause... but adding them explicitly keeps
            # things nice and clear. see below in the body of _isSingleIf() for where
            # to change this...
            ctxt.testlevel = 0
            if _isSingleIf(ctxt, self.match):
                Block(self.match, explicit=True).js(ctxt)
            else:
                self.match.js(ctxt)
            ctxt.indent -= 1
        else:
            ctxt.write(ctxt.indent + '{}\n')
        if self.nomatch is not None:
            if isinstance(self.nomatch, If):
                ctxt.testlevel = 1
                self.nomatch.js(ctxt)
            else:
                ctxt.testlevel = 0
                ctxt.write(ctxt.indent + 'else\n')
                ctxt.indent += 1
                self.nomatch.js(ctxt)
                ctxt.indent -= 1
        ctxt.testlevel = priortestlevel


def _isSingleIf(ctxt, item):
    if isinstance(item, If):
        # TODO: add a compiler flag for disabling "extra safe" braces...
        #      ie. with:
        #
        #        return item.nomatch is None
        #
        #      the following:
        #
        #        if ( A )
        #        {
        #          if ( B )
        #            x();
        #          else
        #            y();
        #        }
        #
        #      will be turned into:
        #
        #        if ( A )
        #          if ( B )
        #            x();
        #          else
        #            y();
        #
        #      despite being semantically identical.
        return True
    if not isinstance(item, Block):
        return False
    children = list(item.children)
    if len(children) > 1:
        return False
    return _isSingleIf(ctxt, children[0])
