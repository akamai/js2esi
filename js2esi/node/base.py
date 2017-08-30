""" js2esi.node.base
defines the most elemental piece of the node abstraction: an node Item.
"""

from __future__ import generators

from js2esi.node import util

__author__ = "Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class StructureError(Exception): pass


def _getSubItems(item):
    if item is None:
        return
    if isinstance(item, Item):
        yield item
        return
    if isinstance(item, str):
        return
    try:
        # try it as a dict-like object...
        for k, v in item.items():
            for i in _getSubItems(k):
                yield i
            for i in _getSubItems(v):
                yield i
    except AttributeError:
        pass
    try:
        # try it as a list-like object...
        for v in item:
            for i in _getSubItems(v):
                yield i
    except TypeError:
        pass
    return


def _resolveProxies(item):
    if item is None:
        return item
    if isinstance(item, Item):
        if item._proxy is not None:
            return _resolveProxies(item._proxy)
        item.__dict__ = _resolveProxies(item.__dict__)
        return item
    if isinstance(item, str):
        return item
    try:
        # try it as a dict-like object...
        newdict = {}
        for k, v in item.items():
            newdict[_resolveProxies(k)] = _resolveProxies(v)
        return newdict
    except AttributeError:
        pass
    try:
        # try it as a list-like object...
        return [_resolveProxies(e) for e in item]
    except TypeError:
        pass
    return item


class Item(object):
    def __init__(self, *args, **kwargs):
        self._proxy = None

    def __esi__(self, context):
        raise NotImplementedError('%s.__esi__' % self.__class__.__name__)

    def esi(self, context, isvars=False):
        nodehier = getattr(context, 'nodehier', [])
        pisvars = context.isvars
        context.isvars = isvars
        context.nodehier = nodehier + [self]
        self.__esi__(context)
        context.nodehier = nodehier
        context.isvars = pisvars
        return self

    def esibuf(self, context=None):
        if context is None:
            context = util.Context()
        context.push_buffered()
        self.esi(context)
        return context.pop_buffered()

    def __js__(self, context):
        raise NotImplementedError('%s.__js__' % self.__class__.__name__)

    def js(self, context):
        nodehier = getattr(context, 'nodehier', [])
        context.nodehier = nodehier + [self]
        self.__js__(context)
        context.nodehier = nodehier
        return self

    def jsbuf(self, context=None):
        if context is None:
            context = util.Context()
        context.push_buffered()
        self.js(context)
        return context.pop_buffered()

    @property
    def __label__(self):
        return 'node.%s' % (self.__class__.__name__,)

    def __str__(self):
        sub = list(self.children)
        ret = self.__label__
        if len(sub) <= 0:
            return ret + '\n'
        ret += ':\n'
        for c in sub:
            ret += '  - ' + '\n    '.join(str(c).strip().split('\n')) + '\n'
        return ret

    @property
    def children(self):
        for k, v in self.__dict__.items():
            if k == '_proxy':
                continue
            for i in _getSubItems(v):
                yield i

    def optimize(self, level=7):
        '''
        Optimize this node node (and all of it\'s children). The ``level``
        parameter indicates how aggressively to optimize the tree - with the
        trade-off being time-to-finish. Currently, the following levels exist:
          3+: collapse all literals, e.g. 3+4 becomes 7
          5+: resolve inline functions
          6+: (TODO) inline hardcoded variable values (but keep declarations)
          7+: (TODO) examine all functions for inline-ability, but keep
              definitions around (in case this script gets included via "eval")
          8:  (TODO) remove auto-inlined functions and unused variables
          9:  (TODO) rename functions and variables to be shorter
        '''
        from js2esi.node import util
        from js2esi.node.function import FunctionDefinition
        from js2esi.node.expression import FunctionCall, Operator, Not
        from js2esi.node.literal import Literal

        ret = self

        if level < 5:
            # un-inline all inline functions
            for fdef in util.allchildren(ret, FunctionDefinition):
                fdef.inline = False
        else:
            inlines = {}
            for fdef in util.allchildren(ret, FunctionDefinition, lambda f: f.inline):
                inlines[fdef.name] = fdef
            # tbd: see below for comments on better ways of detecting recursively
            #      inlined functions... instead of states, i could use a stack of
            #      inlining functions.
            # TODO: this process seems *much* more processor intensive that it needs to
            #      be... need to review exactly why this is necessary...
            # process:
            #   - first iteratively resolve inlines within inlined function definitions
            #     (this is to create completely self-contained inlined function defs)
            #     note that this loop is so that at each step, inlining only happens
            #     for function calls to function definitions that do not, in turn, also
            #     inline. this is for two reasons: a) prevent recursive loops, and b)
            #     keep the inlining process simple since i don't need to worry about
            #     recursive inlining.
            #   - then resolve inlines everywhere else
            count = 0
            changed = True
            while changed:
                count += 1
                changed = False
                if count > 1000:
                    raise StructureError('resolving inlined functions appears to have entered an infinite loop')
                for fdef in inlines.values():
                    # print >>sys.stderr,'check-inline:',fdef
                    for fcall in util.allchildren(fdef, FunctionCall, lambda fc: fc.name in inlines):
                        ok2inline = True
                        subfdef = inlines[fcall.name]
                        for subfcall in util.allchildren(subfdef, FunctionCall, lambda fc: fc.name in inlines):
                            ok2inline = False
                            # print >>sys.stderr,'!ok2inline: %s => %s' % (fdef.name, subfdef.name)
                            break
                        if not ok2inline:
                            continue
                        subfdef.inlineInto(fcall)
                        changed = True
                if changed:
                    ret = _resolveProxies(ret)
                    # TODO: do i need to rebuild the inlines dictionary?...
            # check that all inlined functions are self-contained...
            for fdef in inlines.values():
                for fcall in util.allchildren(fdef, FunctionCall, lambda fc: fc.name in inlines):
                    raise StructureError('recursive inlined function %s() detected' % (fdef.name,))
            while True:
                # tbd: do i need an infinite loop check?
                changed = False
                for call in util.allchildren(ret, FunctionCall, lambda fc: fc.name in inlines):
                    inlines[call.name].inlineInto(call)
                    changed = True
                    ret = _resolveProxies(ret)
                    break
                if not changed:
                    break

        if level >= 3:
            # collapse literals
            # tbd: instead of just limiting the loops to 1000, should
            #      i detect thrashing?... ie.:
            #        initial state A.
            #        first loop: state A changes to state B.
            #        second loop: state B changes to state A.
            #        and we are now in an infinite loop...
            #      instead of limiting this to 1000 loops, should i
            #      detect equivalent states?...
            count = 0
            changed = True
            while changed:
                count += 1
                if count > 1000:
                    raise StructureError('collapsing literals appears to have entered an infinite loop')
                changed = False
                for op in util.allchildren(ret, Operator):
                    if isinstance(op, Not):
                        # TODO: !(Literal(boolean)) can be optimized...
                        continue
                    # TODO: handle other operators, such as bitwise?...
                    # TODO: better strategy: do a "try" with python... if it succeeds,
                    #      use that, otherwise just leave it as is... note that then
                    #      i could combine types, for example ('-' * 6) ==> '------'
                    handlers = {
                        '+': lambda a, b: a + b,
                        '-': lambda a, b: a - b,
                        '*': lambda a, b: a * b,
                        '/': lambda a, b: a / b,
                        '%': lambda a, b: a % b,
                    }
                    if op.op not in handlers:
                        continue
                    lits = None
                    for arg in op.args:
                        if not isinstance(arg, Literal):
                            lits = None
                            break
                        if lits is None:
                            lits = arg.type
                        else:
                            if lits != arg.type:
                                lits = None
                                break
                    if lits is None:
                        continue
                    # tbd: i should really use map/reduce here...
                    val = op.args[0].value
                    for arg in op.args[1:]:
                        val = handlers[op.op](val, arg.value)
                    op._proxy = Literal(str(val)[-2:] == '.0' and int(val) or val)
                    changed = True

                ret = _resolveProxies(ret)

        return ret
