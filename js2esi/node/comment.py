#!/usr/bin/env python
""" js2esi.node.statement
logical statements abstraction
"""
from js2esi.node.statement import Statement

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class Comment(Statement):
    def __init__(self, message):
        super(Comment, self).__init__()
        self.message = message

    def __esi__(self, ctxt):
        ctxt.write('<esi:comment text="%s"/>' % (self.message,))

    def __js__(self, ctxt):
        # cooperation here with statement.Block to add a terminator between
        # consecutive comments
        fc = getattr(ctxt, 'firstcomment', None)
        if fc is not None and fc != self:
            ctxt.write(ctxt.indent + '//\n')
        # TODO: do some escaping?...
        ctxt.write(ctxt.indent + '//### ')
        ctxt.write(('\n%s//### ' % ctxt.indent).join(self.message.split('\n')))
        ctxt.write('\n')
        return self
