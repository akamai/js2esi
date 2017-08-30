""" js2esi.node.statement
logical statements abstraction
"""
from js2esi.node.base import Item
from js2esi.node import util

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class Statement(Item): pass


class BlockFragment(Statement):
    def __init__(self, *statements):
        super(BlockFragment, self).__init__()
        self.statements = []
        for st in statements:
            self.append(st)

    def append(self, statement):
        if statement is None:
            return self
        if statement.__class__ != Block:
            self.statements.append(statement)
        else:
            for s in statement.statements:
                self.append(s)
        return self

    def __esi__(self, ctxt):
        for st in self.statements:
            st.esi(ctxt)

    def __js__(self, ctxt):
        from js2esi.node.expression import FunctionCall
        for st in self.statements:
            if isinstance(st, FunctionCall):
                # tbd: is this the right way, or should FunctionCall know when it
                #      is in "inline" context?... then all inline contexts would
                #      have to broadcast that!... ugh.
                ctxt.write(str(ctxt.indent))
                st.js(ctxt)
                ctxt.write(';\n')
            else:
                st.js(ctxt)


class Block(BlockFragment):
    def __init__(self, *statements, **kwargs):
        super(Block, self).__init__(*statements)
        util.assertOnlyKeywords(kwargs, 'explicit')
        # TODO: this "explicit" is a total *HACK*... it is there so that the
        #      If statement can force "{}" clamping of the Block...
        self.explicit = kwargs.get('explicit', False)

    def __js__(self, ctxt):
        from js2esi.node.variable import Assign
        from js2esi.node.comment import Comment
        sts = self.statements
        if len(sts) <= 0:
            return ctxt.write(ctxt.indent + '{}\n')
        if len(sts) == 1 and not isinstance(sts[0], Comment) and not self.explicit:
            return BlockFragment.__js__(self, ctxt)
        # grouping consecutive statement types, in order to:
        #   - align the "=" of assignment statements
        #   - separate consecutive comments so that they won't be glued
        #     together as a single multi-line on the round trip...
        groups = [BlockFragment(sts[0])]
        for idx, st in enumerate(sts[1:]):
            if st.__class__ != groups[-1].statements[-1].__class__:
                groups.append(BlockFragment(st))
                continue
            groups[-1].append(st)
        for group in groups:
            if isinstance(group.statements[0], Assign):
                group.maxwid = 0
                for st in group.statements:
                    group.maxwid = max(group.maxwid, st.width(ctxt))
                continue
            if isinstance(group.statements[0], Comment):
                group.firstcomment = group.statements[0]
        outdent = int(ctxt.indent) >= 1
        if outdent:
            ctxt.indent -= 1
        ctxt.write(ctxt.indent + '{\n')
        ctxt.indent += 1
        for st in groups:
            ctxt.assignwidth = 0
            if hasattr(st, 'maxwid'):
                ctxt.assignwidth = st.maxwid
            ctxt.firstcomment = getattr(st, 'firstcomment', None)
            st.js(ctxt)
        ctxt.indent -= 1
        ctxt.write(ctxt.indent + '}\n')
        if outdent:
            ctxt.indent += 1


class Output(BlockFragment):
    # tbd: 'vars' should be auto-detectable... especially now that i have
    #      context.nodehier[]... the issue with doing that is that sometimes
    #      it will be unwanted, eg:
    #        printraw('<esi:vars>');
    #        print(myVar, myFuncCall());
    #        print('some other stuff');
    #        printraw('</esi:vars>');

    def __init__(self, *statements, **kwargs):
        super(Output, self).__init__()
        self.raw = kwargs.get('raw', False)
        self.vars = kwargs.get('vars', False)
        for s in statements:
            self.append(s)
        if len(set(kwargs.keys()) - set(('raw', 'vars'))) > 0:
            raise TypeError('unexpected keyword arguments: %s'
                            % (', '.join(set(kwargs.keys()) - set(('raw', 'vars'))),))

    def append(self, s):
        from js2esi.node.literal import Literal
        s = util.expr(s)
        if self.raw and not isinstance(s, Literal):
            raise TypeError('"printraw" function can only accept literal values (e.g. strings and numbers), not "%s"'
                            % (s.__class__.__name__,))
        BlockFragment.append(self, s)

    def __esi__(self, ctxt):
        # tbd: as an optimization, check to see if the Block is a single
        #      variable, in which case, it can be:
        #        <esi:vars name="SYMBOL"/>
        if self.vars:
            ctxt.write('<esi:vars>')
        if self.raw:
            for s in self.statements:
                ctxt.write(str(s.value))
        else:
            for s in self.statements:
                s.esi(ctxt, isvars=True)
        if self.vars:
            ctxt.write('</esi:vars>')

    def __js__(self, ctxt):
        # TODO: i think this can be made into a single "printv()" call...
        #      however, it should inspect the number & size of the output
        #      to see if it should resort to the repetetive invocation...
        # note: the reason to call __js__() instead of js() is that js()
        #       will inject an artificial 'Block' into the node hierarchy.
        from js2esi.node.expression import FunctionCall
        from js2esi.node.literal import Literal
        if len(self.statements) == 1 and not self.raw:
            return Block(FunctionCall(self.vars and 'printv' or 'print',
                                      self.statements[0])).__js__(ctxt)
        sts = [FunctionCall(self.raw and 'printraw' or 'print', e)
               for e in self.statements]
        if self.vars:
            sts.insert(0, FunctionCall('printraw', Literal('<esi:vars>')))
            sts.append(FunctionCall('printraw', Literal('</esi:vars>')))
        return Block(*sts).__js__(ctxt)

