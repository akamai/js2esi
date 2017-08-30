from __future__ import print_function  # this is here for the version check to work on Python 2.

import argparse
import sys

# This must be at the very top, before importing anything else that might break!
# Keep all other imports below with the 'noqa' magic comment.
if sys.version_info < (3, 5):
    print("#" * 49, file=sys.stderr)
    print("# js2esi only supports Python 3.5 and above! #", file=sys.stderr)
    print("#" * 49, file=sys.stderr)

import errno  # noqa
import os  # noqa
import io  #noqa

from js2esi.tools import util  # noqa
from ply import lex, yacc   # noqa
from js2esi.token import ctokens, cparser, dtokens, dparser  # noqa
from js2esi import node  # noqa


__author__ = "Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


class CompilationErrors(Exception):
    def __init__(self, count):
        self.errcnt = count
        super(CompilationErrors, self).__init__('compilation failed with %d error(s)' % (count,))


class DecompilationErrors(CompilationErrors):
    def __init__(self, count):
        self.errcnt = count
        super(CompilationErrors, self).__init__('decompilation failed with %d error(s)' % (count,))


# compute column.
#   input is the input text string
#   tok   is a LexToken instance
def getTokenColumn(input, tok):
    return getDataColumn(input, tok.lexpos)


def getDataColumn(input, lexpos):
    last_cr = input.rfind('\n', 0, lexpos)
    if last_cr < 0:
        last_cr = -1
    col = lexpos - last_cr
    return col


def makeErrorHandler(lexer):
    def errorHandler(msg, lexpos=None, abort=None):
        if lexpos is None:
            lexpos = lexer.lexpos
        lexer.errcnt += 1
        lexer.errfp.write('%s@%d,%d: ERROR: %s\n' \
                          % (lexer.filename, lexer.lineno, getDataColumn(lexer.data, lexpos), msg,))
        if abort is not None:
            raise abort(msg)

    return errorHandler


class Context(object):
    def __init__(self):
        self.lib = []
        self.imports = []


def js2node(context, src):
    # build the lexer
    lexer = lex.lex(module=ctokens)

    # pull in the script
    lexer.filename = context.filename
    lexer.data = src.read()
    lexer.errcnt = 0
    lexer.errfp = context.errfp
    lexer.error = makeErrorHandler(lexer)
    lexer.getcol = lambda t: getTokenColumn(t.lexer.data, t)

    if context.options.lex:
        # output lexer tokens
        result = []
        lexer.input(lexer.data)
        state = 'INITIAL'
        for token in lexer:
            line = '[%d,%d] %s: %r' \
                   % (token.lineno, getTokenColumn(lexer.data, token),
                      token.type, token.value)
            if state != lexer.lexstate:
                line += ' (next state: %s)' % ({'INITIAL': 'initial'}.get(lexer.lexstate, lexer.lexstate),)
                state = lexer.lexstate
            result.append(line)
        return result

    # build the parser
    # yacc(method='LALR', debug=1, module=None, tabmodule='parsetab',
    #      start=None, check_recursion=1, optimize=0, write_tables=1,
    #      debugfile='parser.out', outputdir='', debuglog=None,
    #      errorlog=None, picklefile=None)
    parser = yacc.yacc(module=cparser, tabmodule='cparsetab', debug=0)
    lexer.parser = parser

    # yaccmode
    result = parser.parse(lexer.data, debug=0)

    if lexer.errcnt > 0:
        raise CompilationErrors(lexer.errcnt)

    return result


def node2esi(context, src, dst):
    if context.options.warn:
        dst.write('<esi:comment text="\n')
        dst.write('---- WARNING: GENERATED ESI ----')
        dst.write('\n"/>')

    ctxt = node.Context()
    ctxt.out = dst
    src.esi(ctxt)


def esi2node(context, src):
    # build the lexer
    lexer = lex.lex(module=dtokens)

    # pull in the script
    lexer.filename = context.filename
    lexer.data = src.read()
    lexer.errcnt = 0
    lexer.errfp = context.errfp
    lexer.error = makeErrorHandler(lexer)
    lexer.getcol = lambda t: getTokenColumn(t.lexer.data, t)

    if context.options.lex:
        # output lexer tokens
        result = []
        lexer.input(lexer.data)
        state = 'INITIAL'
        for token in lexer:
            line = '[%d,%d] %s: %r' \
                   % (token.lineno, getTokenColumn(lexer.data, token),
                      token.type, token.value)
            if state != lexer.lexstate:
                line += ' (next state: %s)' % ({'INITIAL': 'initial'}.get(lexer.lexstate, lexer.lexstate),)
                state = lexer.lexstate
            result.append(line)
        return result

    # build the parser
    # yacc(method='LALR', debug=1, module=None, tabmodule='parsetab',
    #      start=None, check_recursion=1, optimize=0, write_tables=1,
    #      debugfile='parser.out', outputdir='', debuglog=None,
    #      errorlog=None, picklefile=None)
    parser = yacc.yacc(module=dparser, tabmodule='dparsetab', debug=0)
    lexer.parser = parser

    # yaccmode
    result = parser.parse(lexer.data, debug=0)

    if lexer.errcnt > 0:
        raise DecompilationErrors(lexer.errcnt)

    return result


def node2js(context, src, dst):
    ctxt = node.Context()
    ctxt.out = dst
    src.js(ctxt)


def resolveImports(context, tree):
    frompath = context.filename
    for imp in node.util.allchildren(tree):
        if not isinstance(imp, node.Import):
            continue
        if imp.inline is not None:
            continue
        if context.options.verbose:
            context.errfp.write('[  ] resolving import of "%s" from "%s"...\n' % (imp.src, frompath))
        fp = None
        for lib in context.lib + [os.path.dirname(frompath)]:
            path = os.path.abspath(os.path.join(lib, imp.src))
            try:
                fp = io.open(path, 'r')
            except Exception as e:
                if context.options.verbose >= 3:
                    if hasattr(e, 'errno') and e.errno == errno.ENOENT:
                        context.errfp.write('[  ]   tried "%s" and failed: file not found\n' % (path,))
                    else:
                        context.errfp.write('[  ]   tried "%s" and failed: %s\n' % (path, e))
                fp = None
                continue
            break
        if fp is None:
            context.errfp.write('[**] ERROR: could not find import "%s"\n' % (imp.src,))
            raise CompilationErrors(1)
        realpath = os.path.realpath(path)
        if not imp.force and realpath in context.imports:
            if context.options.verbose >= 2:
                context.errfp.write('[  ] skipping import of "%s" (already imported)\n' % (path,))
            # tbd: *HACKALERT*... this is really just letting the "la
            imp.inline = node.Block()
            continue
        if context.options.verbose:
            context.errfp.write('[  ] importing "%s"...\n' % (path,))
        context.filename = path
        subtree = js2node(context, fp)
        fp.close()
        context.imports.append(realpath)
        resolveImports(context, subtree)
        imp.inline = subtree


def common_options():
    parser = argparse.ArgumentParser(usage="%(prog)s [options] <src>",
                                     description='compiles js syntax into esi output',)

    parser.add_argument(
        '--version',
        action='store_true',
        help="show version number and exit",
        dest='version',
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true", dest="quiet",
        help="Quiet."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count", dest="verbose", default=0,
        help="Increase log verbosity. (multiple invocations increase verbosity)"
    )
    parser.add_argument(
        "-w", "--no-warning",
        action="store_false", dest="warn",
        help="disable generated ESI warning."
    )
    parser.add_argument('-l', '--lex',
                        action='store_true', dest='lex', default=False,
                        help='display lexical tokens instead of parsing')

    parser.add_argument('-L', '--library',
                        action='append', dest='lib', default=[],
                        help='add the specified directory to the JSLIB lookup path')

    parser.add_argument('-n', '--node',
                        action='store_true', dest='node', default=False,
                        help='display the resulting Abstract Syntax Tree instead'
                             ' of the JS/ESI')

    parser.add_argument('-d', '--decompile',
                        action='store_true', dest='decompile', default=False,
                        help='decompile ESI to js')

    parser.add_argument('-O', '--optimize', metavar='LEVEL',
                        action='store', dest='optlevel', default=7, type=int,
                        help='optimization level (range: 0 to 9,'
                             ' default: 7) - note that level 9 should only'
                             ' be used for completely independent ESI scripts')
    parser.add_argument('filename', type=argparse.FileType('r'),
                        help='inputfilename', default=sys.stdin)

    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        help='outputfilename', default=sys.stdout)

    return(parser)


def process_options(args, extra=None):  # pragma: no cover

    parser = common_options()
    options = parser.parse_args(args)

    context = Context()
    context.options = options
    context.src = options.filename
    context.filename = options.filename.name
    context.errfp = sys.stderr

    context.lib = os.environ.get('JSLIB', '').split(':') + options.lib
    context.lib = [e for e in context.lib if len(e) > 0]
    context.imports = []

    # if '.' not in context.js2esi and os.environ.get('JSLIB', None) != '':
    #   context.js2esi += ['.']

    if options.version:
        print(util.dump_system_info())
        sys.exit(0)
    if options.quiet :
        options.verbosity = 0

    return(context)


def esi2js(args=None):  # pragma: no cover
    context = process_options(args)
    try:
        # TODO: warn user about not supporting correct precedence rules?...

        if context.options.verbose:
            print('[  ] decompiling "%s"...' % (context.filename,), file=sys.stderr)
        tree = esi2node(context, context.src)
        if context.options.lex:
            for e in tree:
                sys.stdout.write(e)
                sys.stdout.write('\n')
        elif context.options.node:
            sys.stdout.write(str(tree))
        else:
            node2js(context, tree, sys.stdout)
    except CompilationErrors as e:
        return 100 + e.errcnt

def js2esi(args=None):  # pragma: no cover
    context = process_options(args)
    try:
        # TODO: warn user about not supporting correct precedence rules?...
        if context.options.verbose:
            print('[  ] compiling "%s"...' % (context.filename,), file=sys.stderr)
            if len(context.lib) <= 0:
                print('[  ] library include path is empty', file=sys.stderr)
            else:
                print('[  ] library include path (in order of precedence):', file=sys.stderr)
                for lib in context.lib:
                    print('[  ]  ', lib, file=sys.stderr)
        tree = js2node(context, context.src)
        if context.options.lex:
            for e in tree:
                sys.stdout.write(e)
                sys.stdout.write('\n')
        elif context.options.node:
            sys.stdout.write(str(tree))
        else:
            resolveImports(context, tree)
            tree.optimize(context.options.optlevel)
            # TODO:
            # if options.verbose:
            #   print >>sys.stderr, '[  ] resolving inlined functions...'
            node2esi(context, tree, sys.stdout)
    except CompilationErrors as e:
        return 100 + e.errcnt

if __name__ == '__main__':
    sys.exit(js2esi())
