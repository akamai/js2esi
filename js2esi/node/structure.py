""" js2esi.node.structure
logical structures (lists, dictionaries) abstraction
"""
from js2esi.node.expression import Expression
from js2esi.node import util

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class List(Expression):
    def __init__(self, *args):
        super(List, self).__init__()
        self.elements = []
        for e in args:
            self.append(e)

    def append(self, element):
        self.elements.append(element)

    def __esi__(self, ctxt):
        ctxt.write('[')
        for idx, el in enumerate(self.elements):
            if idx != 0:
                ctxt.write(',')
            el.esi(ctxt)
        ctxt.write(']')

    def __js__(self, ctxt):
        ctxt.write('[')
        for idx, el in enumerate(self.elements):
            if idx != 0:
                ctxt.write(', ')
            el.js(ctxt)
        ctxt.write(']')


Array = List


class Dictionary(Expression):
    def __init__(self, *args):
        super(Dictionary, self).__init__()
        self.elements = []
        for e in args:
            self.append(e)

    def append(self, pair):
        self.elements.append(pair)

    def __esi__(self, ctxt):
        ctxt.write('{')
        for idx, el in enumerate(self.elements):
            if idx != 0:
                ctxt.write(',')
            util.expr(el[0]).esi(ctxt)
            ctxt.write(':')
            el[1].esi(ctxt)
        ctxt.write('}')

    def __js__(self, ctxt):
        ctxt.write('{')
        for idx, el in enumerate(self.elements):
            if idx != 0:
                ctxt.write(', ')
            util.expr(el[0]).js(ctxt)
            ctxt.write(': ')
            el[1].js(ctxt)
        ctxt.write('}')


Dict = Dictionary
Hash = Dictionary

