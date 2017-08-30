
""" Tests compilation/decompilation of respectively JS-to-ESI and
ESI-to-JS.

Also provides python 2.7 ``unittest.TestCase.assertMultiLineEqual()``
functionality to previous versions of python: use the
``MultiLineEqual`` mix-in. The EsiEqual mix-in provides for slightly
more intelligent ESI comparisons... well, much stress on "slightly"
since it currently only improves the difference display.

It also provides the DataHandler for urllib2 so that "data:" URL
schemes can be loaded.

"""

import difflib
import io
import os
import re
import sys
import unittest

from js2esi import node
from js2esi.token.adict import adict
from js2esi.tools import main as cli

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class MultiLineEqual:
    def assertMultiLineEqual(self, chk, tgt, msg=None):
        try:
            # this can be re-entrant so we must go up to the original base class
            super(TestJs2Esi, self).assertMultiLineEqual(chk, tgt)
            # self.assertEqual(chk, tgt)
            return
        except Exception:
            if not type(chk) is str or not type(tgt) is str:
                raise
        print ('%s, diff:' % (msg or 'FAIL',), file=sys.stderr)
        print ('--- expected', file=sys.stderr)
        print ('+++ received', file=sys.stderr)
        differ = difflib.Differ()
        diff = list(differ.compare(chk.split('\n'), tgt.split('\n')))
        cdiff = []
        need = -1
        for idx, line in enumerate(diff):
            if line[0] != ' ':
                need = idx + 2
            if idx > need \
                    and line[0] == ' ' \
                    and (len(diff) <= idx + 1 or diff[idx + 1][0] == ' ') \
                    and (len(diff) <= idx + 2 or diff[idx + 2][0] == ' '):
                continue
            if idx > need:
                cdiff.append('@@ %d @@' % (idx + 1,))
                need = idx + 2
            cdiff.append(line)
        for line in cdiff:
            print (line, file=sys.stderr)
            # super(TestJs2Esi, self).assertEqual('expected', 'received')


class EsiEqual(MultiLineEqual):
    def assertEqualEsi(self, expected, received, msg=None):
        try:
            self.assertEqual(expected, received)
            return
        except Exception:
            def n(s):
                return s.replace('><', '>\n<').replace('>$', '>\n$').replace(')<', ')\n<')
            self.maxDiff = None
            self.assertMultiLineEqual(n(str(expected)), n(str(received)), msg)


class TestJs2Esi(unittest.TestCase, EsiEqual):
    def assertMultiLineEqual(self, first, second, msg=None):
        # overriding the python assertMultiLineEqual so that it uses our custom assertMultiLineEqual

        return EsiEqual.assertMultiLineEqual(self, first, second, msg)

    def runTest(self):
        # TODO: figure out why i need this...
        pass

    def js2esi(self, js, level=7):
        context = cli.Context()
        context.filename = '<STRING>'
        context.options = adict.new(verbose=0, lex=False, warn=False)
        context.errfp = sys.stderr  # io.StringIO()
        src = io.StringIO(js)
        out = io.StringIO()
        tree = cli.js2node(context, src)
        cli.resolveImports(context, tree)
        tree.optimize(level)
        cli.node2esi(context, tree, out)
        return out.getvalue()

    def test_inline_tooManyArgs(self):
        js = 'function inline i(x) return x*2; v = i(2, 3);'
        self.assertRaisesRegexp(node.StructureError, 'takes at most 1 argument',
                                self.js2esi, js)

    def test_inline_tooFewArgs(self):
        js = 'function inline i(a, b, c=3) return a+b+c; v = i(2);'
        self.assertRaisesRegexp(node.StructureError, 'does not provide a value for parameter',
                                self.js2esi, js)

    def test_inline_notLiteralOrVariable(self):
        js = 'function inline i(a) return a+2; v = i(1+2);'
        self.assertRaisesRegexp(node.StructureError, 'called with type',
                                self.js2esi, js)

    def test_inline_nonReturnOnly(self):
        js = 'function inline i(x) {if ( x == 2 ) return 4; return x*2;} v = i(2);'
        self.assertRaisesRegexp(node.StructureError, 'a single return statement',
                                self.js2esi, js)

    def test_inline_nonSimpleVariable(self):
        js = 'function inline i(x) return x*2; v = i(d["x"]);'
        self.assertRaisesRegexp(node.StructureError, 'non-simple variable',
                                self.js2esi, js)

    def test_inline_useARGS(self):
        js = 'function inline i(x) return ARGS[0]*2; v = i(2);'
        self.assertRaisesRegexp(node.StructureError, 'cannot use variable "ARGS"',
                                self.js2esi, js)

    def test_noOptimization(self):
        js = 'function inline i(x) {return x*(1+1);} v = i(2);'
        chk = '<esi:function name="i"><esi:assign name="x" value="$(ARGS{0})"/>' \
              '<esi:return value="$(x)*(1+1)"/></esi:function>' \
              '<esi:assign name="v" value="$i(2)"/>'
        self.assertEqualEsi(chk, self.js2esi(js, 0))

    def test_collapseLiteralsOnly(self):
        js = 'function inline i(x) {return x*(1+1);} v = i("str"+"ing");'
        chk = '<esi:function name="i"><esi:assign name="x" value="$(ARGS{0})"/>' \
              '<esi:return value="$(x)*2"/></esi:function>' \
              '<esi:assign name="v" value="$i(\'string\')"/>'
        self.assertEqualEsi(chk, self.js2esi(js, 3))

    def test_inline_ok(self):
        js = 'function inline i(x) {return x*2;} v = i(2);'
        chk = '<esi:assign name="v" value="4"/>'
        self.assertEqualEsi(chk, self.js2esi(js))

    def test_inline_okblock(self):
        js = 'function inline i(x) {return x*2;} v = i(2);'
        chk = '<esi:assign name="v" value="4"/>'
        self.assertEqualEsi(chk, self.js2esi(js))

    def test_inline_withDefault(self):
        js = 'function inline add(a,b,c=3)return a+b+c;v=add(1,2);'
        chk = '<esi:assign name="v" value="6"/>'
        self.assertEqualEsi(chk, self.js2esi(js))


# FILESYSTEM BASED UNIT TESTS



def generateCompileEsiTest(testdirname, testname):
    def t(self=None):
        context = cli.Context()
        context.filename = os.path.join(testdirname, 'test.%s.js' % (testname,))
        context.options = adict.new(verbose=0, lex=False, warn=False)
        context.errfp = io.StringIO()
        out = io.StringIO()
        try:
            tree = cli.js2node(context, io.open(context.filename, 'r'))
            cli.resolveImports(context, tree)
            tree.optimize(7)
            cli.node2esi(context, tree, out)
        except cli.CompilationErrors as e:
            print ('FAIL test.%s.js, %d error(s):' % (testname, e.errcnt,), file=sys.stderr)
            print (context.errfp.getvalue(), file=sys.stderr)
            raise
        chk = io.open(os.path.join(testdirname, 'test.%s.chk' % (testname,)), 'r', newline='').read()
        out = out.getvalue()
        if out != chk:
            if self is not None:
                sys.stderr.write('%s... ' % (testname,))
            TestJs2Esi().assertEqualEsi(chk, out, 'FAIL (js => esi)')
            raise NotImplementedError('unexpected non-fail (js.a)')

        # now try a round-trip, esi => js => esi
        # note: not doing round-trip to the initial js, as that is manually
        #       created and is therefore prone to being different...
        rtsrc = io.StringIO(out)
        rtmid = io.StringIO()
        rtdst = io.StringIO()
        try:
            fn = context.filename
            context.filename = fn + ' (roundtrip: esi to js)'
            context.errfp = io.StringIO()
            cli.node2js(context, cli.esi2node(context, rtsrc), rtmid)
            context.filename = fn + ' (roundtrip: js back to esi)'
            context.errfp = io.StringIO()
            rtmid = io.StringIO(rtmid.getvalue())
            cli.node2esi(context, cli.js2node(context, rtmid), rtdst)
        except cli.CompilationErrors as e:
            print ('FAIL test.%s.js (roundtrip), %d error(s):' % (testname, e.errcnt,), file=sys.stderr)
            print (context.errfp.getvalue(), file=sys.stderr)
            print (context.errfp.getvalue(), file=sys.stderr)
            raise
        rtdst = rtdst.getvalue()
        if rtdst != out:
            if self is not None:
                sys.stderr.write('%s (roundtrip)... ' % (testname,))
            TestJs2Esi().assertEqualEsi(out, rtdst, 'FAIL (js => esi => js => esi)')
            raise NotImplementedError('unexpected non-fail (js.b)')

    t.description = 'test_compile: js2esi/test/test.%s.js' % (testname,)
    t.methodname = 'test_compile_' + re.sub('[^a-zA-Z0-9_]+', '_', testname)
    return t


def generateDecompileEsiTest(testdirname, testname):
    def t(self=None):
        context = cli.Context()
        context.filename = os.path.join(testdirname, 'test.%s.esi' % (testname,))
        context.options = adict.new(verbose=0, lex=False, warn=False)
        context.errfp = io.StringIO()
        out = io.StringIO()
        try:
            # cli.decompile_esi2js(context, io.open(context.filename, 'r'), out)
            cli.node2js(context, cli.esi2node(context, io.open(context.filename, 'r', newline='')), out)
        except cli.CompilationErrors as e:
            print ('FAIL test.%s.esi, %d error(s):' % (testname, e.errcnt,), file=sys.stderr)
            print (context.errfp.getvalue(), file=sys.stderr)
            raise
        chk = io.open(os.path.join(testdirname, 'test.%s.chk' % (testname,)), 'r', newline='').read()
        out = out.getvalue()
        if out != chk:
            if self is not None:
                sys.stderr.write('%s... ' % (testname,))
            TestJs2Esi().assertMultiLineEqual(chk, out, 'FAIL (esi => js)')
            raise NotImplementedError('unexpected non-fail (esi.a)')

        # now try a round-trip, js => esi => js
        # note: not doing round-trip to the initial esi, as that is manually
        #       created and is therefore prone to being different...
        rtsrc = io.StringIO(out)
        rtmid = io.StringIO()
        rtdst = io.StringIO()
        try:
            fn = context.filename
            context.filename = fn + ' (roundtrip: js to esi)'
            context.errfp = io.StringIO()
            cli.node2esi(context, cli.js2node(context, rtsrc), rtmid)
            context.filename = fn + ' (roundtrip: esi back to js)'
            context.errfp = io.StringIO()
            rtmid = io.StringIO(rtmid.getvalue())
            cli.node2js(context, cli.esi2node(context, rtmid), rtdst)
        except cli.CompilationErrors as e:
            print ('FAIL test.%s.esi (roundtrip), %d error(s):' % (testname, e.errcnt,), file=sys.stderr)
            print (context.errfp.getvalue(), file=sys.stderr)
            raise
        rtdst = rtdst.getvalue()
        if rtdst != out:
            if self is not None:
                sys.stderr.write('%s (roundtrip)... ' % (testname,))
            TestJs2Esi().assertMultiLineEqual(out, rtdst, 'FAIL (esi => js => esi => js)')
            raise NotImplementedError('unexpected non-fail (esi.b)')

    t.description = 'test_decompile: js2esi/test/test.%s.esi' % (testname,)
    t.methodname = 'test_decompile_' + re.sub('[^a-zA-Z0-9_]+', '_', testname)
    return t


testdirname = os.path.join(os.path.dirname(__file__), 'test')


# nose unit testing integration...
def test_files():
    # yield generateCompileEsiTest(testdirname, 'js-conditionals-nested')
    # yield generateDecompileEsiTest(testdirname, 'esi-conditionals')
    # return

    for fname in os.listdir(testdirname):
        m = re.match('^test\.(.*)\.js$', fname, re.I)
        if m is not None:
            yield generateCompileEsiTest(testdirname, m.group(1))
        m = re.match('^test\.(.*)\.esi$', fname, re.I)
        if m is not None:
            yield generateDecompileEsiTest(testdirname, m.group(1))


# standard unittest integration...
for t in test_files():
    setattr(TestJs2Esi, t.methodname, t)

if __name__ == '__main__':
    unittest.main()
