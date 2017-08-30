""" js2esi.node.literal
logical literal object (string, number, etc) abstraction
"""
import inspect

from js2esi.node import util
from js2esi.node.statement import Statement
from js2esi.node.structure import List
from js2esi.node.expression import Expression

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class Include(Statement):
    def __init__(self, src, alt=None, dca=None, onError=None, maxWait=None,
                 ttl=None, noStore=None, method=None, entity=None,
                 appendHeader=[], removeHeader=[], setHeader=[], eval=False):
        super(Include, self).__init__()
        self.src = src
        self.alt = alt
        self.dca = dca
        self.onError = onError
        self.maxWait = maxWait
        self.ttl = ttl
        self.noStore = noStore
        self.method = method
        self.entity = entity
        self.appendHeader = appendHeader
        self.removeHeader = removeHeader
        self.setHeader = setHeader
        self.eval = eval

    def getInitParameterList():
        aspec = inspect.getargspec(Include.__init__)
        if 'self' in aspec.args:
            aspec.args.remove('self')
        return aspec.args

    getInitParameterList = staticmethod(getInitParameterList)

    def __esi__(self, ctxt):
        ctxt.write('<esi:%s' % (self.eval and 'eval' or 'include',))
        for k, v in (
                ('src', 'src'),
                ('alt', 'alt'),
                ('dca', 'dca'),
                ('onError', 'onerror'),
                ('maxWait', 'maxwait'),
                ('ttl', 'ttl'),
                ('noStore', 'no-store'),
                ('method', 'method'),
                ('entity', 'entity'),
        ):
            if getattr(self, k, None) is not None:
                # TODO: quote-escape values?!...
                if isinstance(getattr(self, k), Expression):
                    ctxt.push_buffered()
                    getattr(self, k).esi(ctxt, isvars=True)
                    value = ctxt.pop_buffered()
                else:
                    value = str(getattr(self, k))
                # tbd: ugh. this is horrendous. the ghost ESI parser is significantly defective!...
                if k == 'dca' and '>' in value:
                    value = "'%s'" % (value,)
                ctxt.write(' %s="%s"' % (v, value))
        for k, v in (
                ('appendHeader', 'appendheader'),
                ('removeHeader', 'removeheader'),
                ('setHeader', 'setheader'),
        ):
            els = getattr(self, k, None) or []
            if isinstance(els, List):
                els = els.elements
            for el in els:
                # TODO: quote-escape values?!...
                ctxt.write(' %s="' % v)
                el.esi(ctxt, isvars=True)
                ctxt.write('"')
        ctxt.write('/>')

    def __js__(self, ctxt):
        ctxt.write(str(ctxt.indent))
        ctxt.write(self.eval and 'eval(' or 'include(')
        # tbd: format these on multiple lines if there are more than, say, N
        #      parameters?...
        ctxt.write('src=')
        self.src.js(ctxt)
        for arg in self.getInitParameterList():
            if arg in ['src', 'eval']:
                continue
            val = getattr(self, arg, None)
            if val is None or arg.endswith('Header') and len(val) <= 0:
                continue
            ctxt.write(', %s=' % arg)
            if not arg.endswith('Header'):
                util.expr(val).js(ctxt)
                continue
            ctxt.write('[')
            for idx, st in enumerate(val):
                if idx != 0:
                    ctxt.write(', ')
                util.expr(st).js(ctxt)
            ctxt.write(']')
        ctxt.write(');\n')


class Eval(Include):
    def __init__(self, src, **kwargs):
        super(Eval, self).__init__(src=src, eval=True, **kwargs)
