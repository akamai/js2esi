""" js2esi.node.literal
logical package abstraction
"""
from js2esi.node.statement import Statement
from js2esi.node.literal import Literal

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class Import(Statement):
    def __init__(self, src, force=False):
        super(Import, self).__init__()
        self.src = src
        self.force = force
        self.inline = None

    def __esi__(self, ctxt):
        if self.inline is not None:
            self.inline.esi(ctxt)

    def __js__(self, ctxt):
        ctxt.write(ctxt.indent + 'require(')
        Literal(self.src).js(ctxt)
        if self.force:
            ctxt.write(', force=true')
        ctxt.write(');\n')
