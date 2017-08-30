""" js2esi.node.tryexcept
logical try..except abstraction
"""

from js2esi.node.statement import Statement

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class Try(Statement):
    def __init__(self, tryBlock, exceptBlock=None):
        super(Try, self).__init__()
        self.tryBlock = tryBlock
        self.exceptBlock = exceptBlock

    def __esi__(self, ctxt):
        ctxt.write('<esi:try><esi:attempt>')
        self.tryBlock.esi(ctxt)
        ctxt.write('</esi:attempt>')
        if self.exceptBlock is not None:
            ctxt.write('<esi:except>')
            self.exceptBlock.esi(ctxt)
            ctxt.write('</esi:except>')
        ctxt.write('</esi:try>')

    def __js__(self, ctxt):
        ctxt.write(str(ctxt.indent))
        ctxt.write('try\n')
        ctxt.indent += 1
        self.tryBlock.js(ctxt)
        ctxt.indent -= 1
        if self.exceptBlock is not None:
            ctxt.write(str(ctxt.indent))
            ctxt.write('catch(e)\n')
            ctxt.indent += 1
            self.exceptBlock.js(ctxt)
            ctxt.indent -= 1
