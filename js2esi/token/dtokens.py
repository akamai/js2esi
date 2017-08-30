""" js2esi.token.dtokens
 ply.lex token definitions for esi-to-js decompilation
 Generates esi-to-js decompilation lexer tokens. Note the following
token naming pattern:

  sCOMMAND	start ESI open element, eg "<esi:assign"
  oCOMMAND	opening ESI element without attributes, eg "<esi:vars>"
  cCOMMAND	closing ESI element, eg "</esi:vars>"
  eCOMMAND	empty ESI element without attributes, eg "<esi:break/>"
  aATTRIBUTE	begin xml attribute declaration, eg \'name="\'
  xEND		the end of an XML element, \'>\'
  xEMPTY	the end of an empty XML element, \'/>\'

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"

"""

import re

commands = (
    # format: (name, flag:simple)
    ('assign', False),
    ('debug', True),
    ('include', False),
    ('eval', False),
    ('vars', False),
    ('try', True),
    ('attempt', True),
    ('except', True),
    # TODO: implement!
    # ('text', True),
    ('foreach', False),
    ('break', True),
    ('choose', True),
    ('when', False),
    ('otherwise', True),
    ('comment', False),
    # TODO: implement!
    # ('remove', True),
    ('function', False),
    ('return', False),
)

attributes = (
    # assign:
    'name',  # also in: function, vars
    'value',  # also in: return
    # comment:
    'text',
    # include/eval:
    'src',
    'alt',
    'dca',
    'onerror',
    'maxwait',
    'ttl',
    'no-store',
    'appendheader',
    'removeheader',
    'setheader',
    'method',
    'entity',
    # foreach:
    'collection',
    'item',
    # when:
    'test',
    'matchname',
)

# TODO: support <!--esi ... -->

# list of token names
tokens = (
             'xEND',
             'xEMPTY',
             'NUMBER',
             'STRING',
             'WS',
             'DOLLAR',
             'LPAREN',
             'RPAREN',
             'LBRACE',
             'RBRACE',
             'LBRACKET',
             'RBRACKET',
             'PIPE',
             'COMMA',
             'COLON',
             'EQUAL',
             'NOTEQUAL',
             'LESSERTHAN',
             'LESSEROREQUAL',
             'GREATERTHAN',
             'GREATEROREQUAL',
             'PLUS',
             'MINUS',
             'MULTIPLY',
             'MODULUS',
             'DIVIDE',
             'RANGE',
             'NOT',
             'AND',
             'OR',
             'BITWISENOT',
             'BITWISEAND',
             'BITWISEOR',
             'BITWISEXOR',
             'SHIFTLEFT',
             'SHIFTRIGHT',
             'HAS',
             'HAS_I',
             'MATCHES',
             'MATCHES_I',
             'SYMBOL',
             'VARREF',
             'FUNCCALL',
             # tbd; temporarily disabled - see comment below on XMLCOMMENT...
             # 'XMLCOMMENT',
         ) \
         + tuple(['s' + e[0].upper() for e in commands if not e[1]]) \
         + tuple(['o' + e[0].upper() for e in commands if e[1]]) \
         + tuple(['e' + e[0].upper() for e in commands if e[1]]) \
         + tuple(['c' + e[0].upper() for e in commands]) \
         + tuple(['a' + re.sub('[^A-Z]', '', e.upper()) for e in attributes])

# whitespace matcher

ws = re.compile('^\s+$', re.MULTILINE)


# common token methods

def t_simpleEsiOpen(t):
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.value = t.lexer.lexmatch.group('tag')
    t.type = 'o' + t.value.upper()
    if t.value == 'assign':
        t.lexer.push_state('expr')
    else:
        t.lexer.push_state('vars')
    return t


t_simpleEsiOpen.__doc__ = '<esi:(?P<tag>%s)[ \t\n]*>' % '|'.join([e[0] for e in commands if e[1]])


def t_simpleEsiEmpty(t):
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.value = t.lexer.lexmatch.group('tag')
    t.type = 'e' + t.value.upper()
    return t


t_simpleEsiEmpty.__doc__ = '<esi:(?P<tag>%s)[ \t\n]*/>' % '|'.join([e[0] for e in commands if e[1]])


def t_esiStart(t):
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.value = t.lexer.lexmatch.group('tag')
    t.type = 's' + t.value.upper()
    t.lexer.esicommand = t.lexer.lexmatch.group('tag')
    t.lexer.esiopening = True
    t.lexer.esiattr = None
    t.lexer.push_state('xmlattr')
    return t


t_esiStart.__doc__ = '<esi:(?P<tag>%s)[ \t\n]*' % '|'.join([e[0] for e in commands if not e[1]])


def t_esiClose(t):
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.value = t.lexer.lexmatch.group('tag')
    t.type = 'c' + t.value.upper()
    t.lexer.esicommand = None
    t.lexer.esiopening = False
    t.lexer.pop_state()
    return t


t_esiClose.__doc__ = '</esi:(?P<tag>%s)[ \t\n]*>' % '|'.join([e[0] for e in commands])


def t_STRING(t):
    r'<?[^<]+'
    t.lexer.lineno += len(t.value.split('\n')) - 1
    if ws.match(t.value):
        t.type = 'WS'
    return t


# ignore handling rules

t_ignore = ''


# error handling rules
def t_error(t):
    t.lexer.error('illegal lexical character "%s" (in %s context)' % (t.value[0], t.lexer.lexstate))
    t.lexer.skip(1)


# exclusive state: 'xmlattr' (within XML tags - for attributes, etc)

def t_xmlattr_ATTR(t):
    r'"?[ \t\n]*(?P<symbol>[a-zA-Z][a-zA-Z0-9-]*)[ \t\n]*=[ \t\n]*"'
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.value = t.lexer.lexmatch.group('symbol')
    if t.value not in attributes:
        return t
    t.lexer.esiattr = t.value
    t.type = 'a' + re.sub('[^A-Z]', '', t.value.upper())
    if t.lexer.esiattr in ['text', 'matchname']:
        t.lexer.push_state('xmlattrtext')
    elif t.lexer.esiattr in ['src', 'alt', 'dca', 'onerror', 'maxwait',
                             'ttl', 'no-store',
                             'appendheader', 'removeheader', 'setheader',
                             'method', 'entity',
                             ]:
        t.lexer.push_state('xmlattrvars')
    else:
        t.lexer.push_state('xmlattrvalue')
    return t


# def t_xmlattr_XQUOTE(t):
#   '"'
#   # tbd: technically, matchname should look for SYMBOLs, but xmlattrtext should do the trick...
#   if t.lexer.esiattr in ['text', 'matchname']:
#     t.lexer.push_state('xmlattrtext')
#   elif t.lexer.esiattr in ['src', 'alt', 'dca', 'onerror', 'maxwait',
#                            'ttl', 'no-store',
#                            'appendheader', 'removeheader', 'setheader',
#                            'method', 'entity',
#                            ]:
#     t.lexer.push_state('xmlattrvars')
#   else:
#     t.lexer.push_state('xmlattrvalue')
#   return t

def t_xmlattr_xEND(t):
    '"?[ \t\n]*>'
    t.lexer.lineno += len(t.value.split('\n')) - 1
    # t.lexer.esicommand = None
    # t.lexer.pop_state()
    # return t

    # tbd: this is a *hack*... i pop states until i have popped 'xmlattr'
    while t.lexer.lexstate != 'xmlattr':
        t.lexer.pop_state()

    if t.lexer.esiopening:
        t.lexer.pop_state()
        if t.lexer.esicommand in ['assign']:
            t.lexer.push_state('expr')
        else:
            t.lexer.push_state('vars')
    else:
        t.lexer.esicommand = None
        t.lexer.pop_state()
    return t


def t_xmlattr_xEMPTY(t):
    '"?[ \t\n]*/>'
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.lexer.esicommand = None

    # tbd: this is a *hack*... i pop states until i have popped 'xmlattr'
    while t.lexer.lexstate != 'xmlattr':
        t.lexer.pop_state()

    t.lexer.pop_state()
    return t


# def t_xmlattr_OTHER(t):
#   r'.+'
#   t.lexer.pop_state()
#   t.lexer.lineno -= len(t.lexer.lexdata[t.lexer.mclast:t.lexer.lexpos].split('\n')) - 1
#   t.lexer.skip(t.lexer.mclast - t.lexer.lexpos)

# def t_xmlattr_newline(t):
#   r'\n+'
#   t.lexer.lineno += len(t.value)

t_xmlattr_ignore = ''
t_xmlattr_error = t_error


# exclusive state: 'xmlattrvalue' (for expressions in XML attributes)
# exclusive state: 'expr' (for expressions in text nodes)
# exclusive state: 'exprlist' (for expressions in function calls)

###
def t_xmlattrvalue_XQUOTE(t):
    '"'
    t.lexer.pop_state()


###  return t

# note: ESI attributes do NOT support the xml escaping sequences.
#       eg. 'test="a && b"' CANNOT be replaced by 'test="a &amp;&amp; b"'

t_xmlattrvalue_expr_exprlist_DOLLAR = r'\$'
t_xmlattrvalue_expr_exprlist_PIPE = r'\|'
t_xmlattrvalue_expr_exprlist_COMMA = ','
t_xmlattrvalue_expr_exprlist_COLON = ':'
t_xmlattrvalue_expr_exprlist_EQUAL = '=='
t_xmlattrvalue_expr_exprlist_NOTEQUAL = '!='
t_xmlattrvalue_expr_exprlist_LESSERTHAN = '<'
t_xmlattrvalue_expr_exprlist_LESSEROREQUAL = '<='
t_xmlattrvalue_expr_exprlist_GREATERTHAN = '>'
t_xmlattrvalue_expr_exprlist_GREATEROREQUAL = '>='
t_xmlattrvalue_expr_exprlist_PLUS = r'\+'
t_xmlattrvalue_expr_exprlist_MINUS = '-'
t_xmlattrvalue_expr_exprlist_MULTIPLY = r'\*'
t_xmlattrvalue_expr_exprlist_MODULUS = r'\%'
t_xmlattrvalue_expr_exprlist_DIVIDE = '/'
t_xmlattrvalue_expr_exprlist_RANGE = r'\.\.'
t_xmlattrvalue_expr_exprlist_NOT = '!'
t_xmlattrvalue_expr_exprlist_AND = '&&'
t_xmlattrvalue_expr_exprlist_OR = r'\|\|'
t_xmlattrvalue_expr_exprlist_BITWISENOT = '~'
t_xmlattrvalue_expr_exprlist_BITWISEAND = '&'
t_xmlattrvalue_expr_exprlist_BITWISEOR = r'\|'
t_xmlattrvalue_expr_exprlist_BITWISEXOR = r'\^'
t_xmlattrvalue_expr_exprlist_SHIFTLEFT = '<<'
t_xmlattrvalue_expr_exprlist_SHIFTRIGHT = '>>'

# regular expression rules for simple tokens
# t_ASSIGN          = '='

# TODO: implement:
#   <<, >>
#   ~, &, |, ^
#   .. (range)

braceNameMap = {
    '{': 'LBRACE',
    '}': 'RBRACE',
    '(': 'LPAREN',
    ')': 'RPAREN',
    '[': 'LBRACKET',
    ']': 'RBRACKET',
}


def t_xmlattrvalue_expr_exprlist_LPAREN(t):
    r'[\(\{\[]'
    t.lexer.push_state('expr')
    t.type = braceNameMap[t.value]
    return t


def t_expr_exprlist_RPAREN(t):
    r'[\)\}\]]'
    t.lexer.pop_state()
    t.type = braceNameMap[t.value]
    return t


def t_xmlattrvalue_expr_exprlist_REGEX(t):
    r'(has|matches)(_i)?'
    t.type = t.value.upper()
    return t


def t_xmlattrvalue_expr_exprlist_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


# tbd: i'm not 100% sure these should be here... i think if an 'expr' is
#      matching these, then it should prolly be a 'vars'...
t_expr_simpleEsiOpen = t_simpleEsiOpen
t_expr_simpleEsiEmpty = t_simpleEsiEmpty
t_expr_esiStart = t_esiStart
t_expr_esiClose = t_esiClose


def t_xmlattrvalue_expr_exprlist_TRIPLEQUOTE(t):
    r'\'\'\'(.|\n)*?\'\'\''
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.value = t.value[3:-3]
    if ws.match(t.value):
        t.type = 'WS'
    else:
        t.type = 'STRING'
    return t


def t_xmlattrvalue_expr_exprlist_STRING(t):
    r'\'([^\'\\]|\\.)*\''
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.value = re.sub('\\\\(.)', '\\1', t.value[1:-1])
    if ws.match(t.value):
        t.type = 'WS'
    return t


def t_xmlattrvalue_expr_exprlist_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_xmlattrvalue_expr_exprlist_SYMBOL(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    return t


# tbd: this is not correct... these states can be pushed in an XML attribute,
#      where XML comments are not legal... ugh.
def t_expr_exprlist_XMLCOMMENT(t):
    r'<!--.*?-->'
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.value = t.value[4:-3]
    # TODO: ignoring these tokens for now... the reason is that max put them in
    #      in places where they really cannot (currently) be serialized into
    #      js... ugh.
    # return t


t_xmlattrvalue_expr_exprlist_ignore = ' \t'
t_xmlattrvalue_expr_exprlist_error = t_error


# exclusive state: 'xmlattrtext' - this is the ... in <esi:comment text="..."/> state

def t_xmlattrtext_STRING(t):
    '[^"]+'
    # TODO: any possibility to escape the dquote (")?...
    t.lexer.lineno += len(t.value.split('\n')) - 1
    if ws.match(t.value):
        t.type = 'WS'
    return t


def t_xmlattrtext_XQUOTE(t):
    '"'
    t.lexer.pop_state()


t_xmlattrtext_ignore = ''
t_xmlattrtext_error = t_error

# exclusive state: 'xmlattrvars' - this is the src/alt tags in eval/include
# exclusive state: 'vars' (content of an XML element, such as <esi:vars>...</esi:vars>)

t_vars_simpleEsiOpen = t_simpleEsiOpen
t_vars_simpleEsiEmpty = t_simpleEsiEmpty
t_vars_esiStart = t_esiStart
t_vars_esiClose = t_esiClose


# def t_vars_esiClose(t):
#   t.lexer.pop_state()
#   return t_esiClose(t)
# t_vars_esiClose.__doc__ = t_esiClose.__doc__

def t_vars_STRING(t):
    r'<?[^$<\\]+'
    # TODO: any possibility to escape the dquote (")?...
    t.lexer.lineno += len(t.value.split('\n')) - 1
    if ws.match(t.value):
        t.type = 'WS'
    return t


def t_xmlattrvars_STRING(t):
    r'[^"$\\]+'
    t.lexer.lineno += len(t.value.split('\n')) - 1
    if ws.match(t.value):
        t.type = 'WS'
    return t


# def t_vars_XMLCOMMENT(t):
#   r'<!--.*?-->'
#   t.lexer.lineno += len(t.value.split('\n')) - 1
#   t.value = t.value[4:-3]
#   # TODO: ignoring these tokens for now... the reason is that max put them in
#   #      in places where they really cannot (currently) be serialized into
#   #      js... ugh.
#   # return t

def t_xmlattrvars_vars_ESCAPE(t):
    r'[\\].'
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.type = 'STRING'
    t.value = t.value[1]
    if ws.match(t.value):
        t.type = 'WS'
    return t


def t_xmlattrvars_vars_ESCAPEFUNC(t):
    r'[$](dollar|dquote|squote)\([ \t\n]*\)'
    t.lexer.lineno += len(t.value.split('\n')) - 1
    t.type = 'STRING'
    if t.value == '$dollar()':
        t.value = '$'
    elif t.value == '$dquote()':
        t.value = '"'
    elif t.value == '$squote()':
        t.value = '\''
    else:
        # this should never happen...
        raise SyntaxError('internal token parsing representational conflict')
    return t


def t_xmlattrvars_vars_VARREF(t):
    r'\$\((?P<symbol>[a-zA-Z_][a-zA-Z_0-9-]+)\)'
    t.value = t.lexer.lexmatch.group('symbol')
    return t


def t_xmlattrvars_vars_VARREF_more(t):
    r'\$\((?P<symbol>[a-zA-Z_][a-zA-Z_0-9-]+)'
    t.value = t.lexer.lexmatch.group('symbol')
    t.type = 'VARREF'
    # tbd: this is prolly not the right state... i should really be detecting
    #      the next char -- either "{" or "|" -- and triggering those as well.
    t.lexer.push_state('expr')
    return t


def t_xmlattrvars_vars_FUNCCALL(t):
    r'\$(?P<symbol>[a-zA-Z_][a-zA-Z_0-9-]+)\('
    t.value = t.lexer.lexmatch.group('symbol')
    t.lexer.push_state('exprlist')
    return t


def t_xmlattrvars_XQUOTE(t):
    '"'
    t.lexer.pop_state()


t_xmlattrvars_vars_ignore = ''
t_xmlattrvars_vars_error = t_error

# states
states = (
    ('xmlattr', 'exclusive'),
    ('xmlattrvalue', 'exclusive'),
    ('xmlattrtext', 'exclusive'),
    ('xmlattrvars', 'exclusive'),
    ('vars', 'exclusive'),
    ('expr', 'exclusive'),
    ('exprlist', 'exclusive'),
)
