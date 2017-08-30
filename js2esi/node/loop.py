""" js2esi.node.structure
logical looping/iteration abstraction
"""
from js2esi.node.statement import Statement

__author__ = "Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class ForEach(Statement):
    # TODO: currently requiring key to be a string...
    def __init__(self, collection, statement, key=None):
        super(ForEach, self).__init__()
        self.key = key
        self.collection = collection
        self.statement = statement
        if self.key is not None and not isinstance(key, str):
            raise TypeError('foreach iteration key must be a string')

    def __esi__(self, ctxt):
        ctxt.write('<esi:foreach collection="')
        # TODO: what about escaping this output?...
        self.collection.esi(ctxt)
        if self.key is None or self.key == 'item':
            ctxt.write('">')
        else:
            ctxt.write('" item="%s">' % (self.key,))
        self.statement.esi(ctxt)
        ctxt.write('</esi:foreach>')

    def __js__(self, ctxt):
        ctxt.write(ctxt.indent + 'for (const %s of ' % (self.key is None and 'item' or self.key,))
        self.collection.js(ctxt)
        ctxt.write(')')
        ctxt.write('\n')
        ctxt.indent += 1
        self.statement.js(ctxt)
        ctxt.indent -= 1


class Break(Statement):
    def __esi__(self, ctxt):
        ctxt.write('<esi:break/>')

    def __js__(self, ctxt):
        ctxt.write(ctxt.indent + 'break;\n')
