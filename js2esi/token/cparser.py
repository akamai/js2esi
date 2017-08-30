""" js2esi.token.cparser.py
ply.yacc parsing definitions for js-to-esi compilation
"""

import base64
from js2esi.token.ctokens import *
import js2esi.node as node
from js2esi.node import helper

__author__ = "Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


def checkNamedArgs(p, args, okargs, funcname):
    for k in args:
        if k not in okargs:
            argmap = dict([(e.lower(), e) for e in okargs])
            dym = ''
            if k.lower() in argmap:
                dym = ' - did you mean "%s"?' % (argmap[k],)
            p.lexer.error('"%s" function does not accept parameter "%s"%s' \
                          % (funcname, k, dym), abort=SyntaxError)


# STATEMENT CONSTRUCTS


start = 'script'


def p_empty(p):
    'empty :'
    pass


def p_script(p):
    '''script : declarations
              | empty'''
    p[0] = p[1]


def p_declarations(p):
    '''declarations : declaration
                    | declarations declaration
                    '''
    if not isinstance(p[1], node.Block):
        p[0] = node.Block(p[1])
    else:
        p[0] = p[1]
    if len(p) > 2:
        p[0].append(p[2])


def p_declaration(p):
    '''declaration : statement
                   | comment
                   | functiondef
                   '''
    p[0] = p[1]


def p_statements_multi(p):
    'statements : statements cstatement'
    if not isinstance(p[1], node.Block):
        p[0] = node.Block(p[1])
    else:
        p[0] = p[1]
    p[0].append(p[2])


def p_statements_mt(p):
    'statements : empty'
    p[0] = node.Block(p[1])


def p_statements_single(p):
    'statements : cstatement'
    p[0] = p[1]


def p_statements_one(p):
    '''cstatement : comment
                  | statement
                  '''
    p[0] = p[1]


def p_statement(p):
    '''statement : assign
                 | try
                 | evalinclude STOP
                 | functioncall STOP
                 | condition
                 | return
                 | functiondef
                 | loop
                 | break
                 | require
                 '''
    # note: "functiondef" is in there only so that round-tripping
    #       works when the initial script is placed in a {..} block...
    # tbd: "break" is in there so that it can exist within a foreach
    #      loop context. better would be for the 'statement' definition
    #      to be context sensitive... maybe something that could be
    #      done with lexer states?...
    p[0] = p[1]


def p_statement_block(p):
    'statement : LBRACE statements RBRACE'
    p[0] = node.Block(p[2])


# COMMENTS


def p_comment(p):
    'comment : ESICOMMENT'
    p[0] = node.Comment(p[1].lstrip())


def p_comment_cont(p):
    'comment : ESICOMMENT commentcont'
    lines = [p[1]] + p[2]
    # strip the largest amount of leading whitespace common to all lines
    while len(lines[0]) > 0 and lines[0][0].isspace():
        newlines = [e[1:] for e in lines if len(e) > 0 and e[0] == lines[0][0]]
        if len(newlines) != len(lines):
            break
        lines = newlines
    p[0] = node.Comment('\n'.join(lines))


def p_commentcont_multi(p):
    'commentcont : commentcont ESICOMMENT_CONT'
    p[0] = p[1] + [p[2]]


def p_commentcont(p):
    'commentcont : ESICOMMENT_CONT'
    p[0] = [p[1]]


# ASSIGNMENT

def p_assign_def(p):
    '''letVar : LET
              | VAR
              | CONST'''
    p[0] = p[1]

def p_assign_strict(p):
    '''assign : letVar assignLvalue ASSIGN expression STOP'''
    p[0] = node.Assign(p[2][0], p[4], key=p[2][1])


def p_assign(p):
    'assign : assignLvalue ASSIGN expression STOP'
    p[0] = node.Assign(p[1][0], p[3], key=p[1][1])


def p_assign_incdec(p):
    '''assign : assignLvalue INCREMENT
              | assignLvalue DECREMENT
              '''
    op = p[2][0] == '+' and node.Plus or node.Minus
    p[0] = node.Assign(p[1][0],
                       op(node.Variable(p[1][0], key=p[1][1]), node.Literal(1)),
                       key=p[1][1])


def p_assign_op(p):
    '''assign : assignLvalue ASSIGNPLUS expression STOP
              | assignLvalue ASSIGNMINUS expression STOP
              | assignLvalue ASSIGNMULTIPLY expression STOP
              | assignLvalue ASSIGNMODULUS expression STOP
              | assignLvalue ASSIGNDIVIDE expression STOP
              '''
    p[0] = node.Assign(p[1][0], node.Operator(p[2][0], node.Variable(p[1][0], key=p[1][1]), p[3]), key=p[1][1])


def p_assignLvalue(p):
    '''assignLvalue : SYMBOL
                    | SYMBOL LBRACKET expression RBRACKET
                    '''
    p[0] = (p[1], len(p) > 3 and p[3] or None)


# IMPORTS


def p_require(p):
    '''require : REQUIRE LPAREN stringLiteral RPAREN STOP
              | REQUIRE LPAREN stringLiteral COMMA namedExpressionList RPAREN STOP
              '''
    kwargs = dict()
    if len(p) > 6:
        kwargs = dict(p[5])
    checkNamedArgs(p,kwargs.keys(), ['force'], 'require')
    p[0] = node.Import(p[3], **kwargs)


# CONDITIONALS


def p_condition_if(p):
    'condition : IF LPAREN testExpression RPAREN statement ifOtherwise'
    p[0] = node.If(p[3], p[5], noMatchStatement=p[6])

#TODO: remove elif
def p_ifOtherwise(p):
    '''ifOtherwise : empty
                   | ELSE IF LPAREN testExpression RPAREN statement ifOtherwise
                   | ELSE statement
                   '''
    p[0] = None
    if len(p) > 7:
        p[0] = node.If(p[4], p[6], noMatchStatement=p[7])
    elif len(p) > 6:
        p[0] = node.If(p[3], p[5], noMatchStatement=p[6])
    elif len(p) > 2:
        p[0] = p[2]


# LOOPS


# javascript `for in` is different than `for of`. A `for in` over an array will return the index,
# the equivelant to a `for of` on a [0..foo.length]
# TODO: support `for in` syntax
def p_foreach_loop(p):
    '''loop : FOR LPAREN letVar SYMBOL OF expression RPAREN statement
            | FOR LPAREN SYMBOL OF expression RPAREN statement
            | FOR LPAREN expression RPAREN statement
            '''
    if len(p) > 8:
        p[0] = node.ForEach(p[6], p[8], key=p[4])
    elif len(p) > 7:
        p[0] = node.ForEach(p[5], p[7], key=p[3])
    else:
        p[0] = node.ForEach(p[3], p[5])


def p_for_loop(p):
    '''statement : FOR LPAREN assign testExpression STOP assign RPAREN statement
            '''
    initAssign = p[3]
    testExpression = p[4]
    statementBlock = node.Block(node.If(node.Not(testExpression), node.Break()))
    statementBlock.statements.append(p[8])
    statementBlock.statements.append(p[6])

    p[0] = node.Block(initAssign)
    p[0].statements.append(node.Assign('_loop', node.List(node.Range(initAssign.value, testExpression.args[1]))))
    p[0].statements.append(node.ForEach(node.Variable('_loop'), statementBlock))


def p_break(p):
    'break : BREAK STOP'
    p[0] = node.Break()


# TRY..EXCEPT BLOCKS
def p_try(p):
    'try : TRY statement'
    p[0] = node.Try(p[2])


def p_tryexcept(p):
    'try : TRY statement EXCEPT statement'
    p[0] = node.Try(p[2], p[4])


def p_trycatch(p):
    'try : TRY statement CATCH LPAREN paramList RPAREN statement'
    p[0] = node.Try(p[2], p[7])


# EVAL/INCLUDE


def p_evalinclude(p):
    '''evalinclude : EVAL LPAREN namedExpressionList RPAREN
                   | EVAL LPAREN namedExpressionList COMMA RPAREN
                   | INCLUDE LPAREN namedExpressionList RPAREN
                   | INCLUDE LPAREN namedExpressionList COMMA RPAREN
                   '''
    kls = p[1] == 'eval' and node.Eval or node.Include
    args = dict(p[3])
    if 'src' not in args:
        p.lexer.error('"%s" requires parameter "src"' % (p[1],), lexpos=p.lexspan(1)[0], abort=SyntaxError)
    checkNamedArgs(p, args.keys(), kls.getInitParameterList(), p[1])
    p[0] = kls(**args)


def p_namedExpressionList(p):
    '''namedExpressionList : empty
                           | namedExpression
                           | namedExpressionList COMMA namedExpression
                           '''
    p[0] = []
    if len(p) > 3:
        p[0] = p[1] + [p[3]]
    elif len(p) > 1 and p[1] is not None:
        p[0].append(p[1])


def p_namedExpression(p):
    'namedExpression : SYMBOL ASSIGN expression'
    p[0] = (p[1], p[3])
    if p[1] in ('appendHeader', 'removeHeader', 'setHeader'):
        if not isinstance(p[0][1], node.List):
            p[0] = (p[1], node.List(p[0][1]))


# FUNCTION DECLARATIONS

def p_functiondef_inline(p):
    # tbd: it would be *great* if i could specify that only "statement"s within
    #      this context could include the "returnStatement"...
    'functiondef : FUNCTION SYMBOL LPAREN paramList RPAREN LBRACE INLINE statements RBRACE'
    p[0] = node.FunctionDefinition(p[2], p[4], node.Block(p[7]), inline=True)

def p_functiondef_jsinline(p):
    # tbd: it would be *great* if i could specify that only "statement"s within
    #      this context could include the "returnStatement"...
    'functiondef : FUNCTION SYMBOL LPAREN paramList RPAREN LBRACE STRING STOP statements RBRACE'
    if p[7] == "inline":
        p[0] = node.FunctionDefinition(p[2], p[4], node.Block(p[9]), inline=True)
    else:
        block = node.Block(p[7]).append(p[9])
        p[0] = node.FunctionDefinition(p[2], p[4], block)

def p_functiondef(p):
    # tbd: it would be *great* if i could specify that only "statement"s within
    #      this context could include the "returnStatement"...
    'functiondef : FUNCTION SYMBOL LPAREN paramList RPAREN statement'
    p[0] = node.FunctionDefinition(p[2], p[4], p[6])


def p_functiondef_inline_old(p):
    # tbd: it would be *great* if i could specify that only "statement"s within
    #      this context could include the "returnStatement"...
    'functiondef : FUNCTION INLINE SYMBOL LPAREN paramList RPAREN statement'
    p[0] = node.FunctionDefinition(p[3], p[5], p[7], inline=True)




def p_paramList_mt(p):
    'paramList : empty'
    p[0] = []


def p_paramList_s(p):
    # parameters are: simple parameters followed by defaulted parameters
    '''paramList : sParamList
                 | sParamList COMMA dParamList
                 | dParamList
                 '''
    p[0] = p[1]
    if len(p) >= 4:
        p[0].extend(p[3])


def p_sParamList(p):
    'sParamList : SYMBOL'
    p[0] = [node.FunctionParam(p[1])]


def p_sParamList_multi(p):
    'sParamList : sParamList COMMA SYMBOL'
    p[0] = p[1] + [node.FunctionParam(p[3])]


def p_dParamList(p):
    'dParamList : SYMBOL ASSIGN literal'
    p[0] = [node.FunctionParam(p[1], default=p[3])]


def p_dParamList_multi(p):
    'dParamList : dParamList COMMA SYMBOL ASSIGN literal'
    p[0] = p[1] + [node.FunctionParam(p[3], default=p[5])]


def p_return(p):
    'return : RETURN expression STOP'
    p[0] = node.FunctionReturn(p[2])



def p_property(p):
    '''property : expression DOT
                  '''
    p[0] = p[1]

def p_noop(p):
    'statement : STOP'


# EXPRESSIONS


precedence = (
    # lowest to highest precedence rules:
    ('left', 'QUESTION', 'COLON'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'BITWISEOR'),
    ('left', 'BITWISEXOR'),
    ('left', 'BITWISEAND'),
    ('nonassoc', 'EQUAL', 'NOTEQUAL'),
    ('nonassoc', 'LESSERTHAN', 'LESSEROREQUAL', 'GREATERTHAN', 'GREATEROREQUAL',
     'HAS', 'HAS_I', 'MATCHES', 'MATCHES_I'),
    ('left', 'SHIFTLEFT', 'SHIFTRIGHT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULTIPLY', 'MODULUS', 'DIVIDE'),
    ('nonassoc', 'NOT', 'BITWISENOT'),
    ('right', 'UMINUS'),  # tbd: add unary "+"
    ('left', 'DOT'),
)


# for reference, here is the c/c++ precedence table (highest to lowest):
#     1     ::                  Scope resolution  Left-to-right
#     2     ++ --               Suffix/postfix increment and decrement
#           ()                  Function call
#           []                  Array subscripting
#           .                   Element selection by reference
#           ->                  Element selection through pointer
#           typeid()            Run-time type information (see typeid)
#           const_cast          Type cast (see const_cast)
#           dynamic_cast        Type cast (see dynamic_cast)
#           reinterpret_cast    Type cast (see reinterpret_cast)
#           static_cast         Type cast (see static_cast)
#     3     ++ --               Prefix increment and decrement     Right-to-left
#           + -                 Unary plus and minus
#           ! ~                 Logical NOT and bitwise NOT
#           (type)              Type cast
#           *                   Indirection (dereference)
#           &                   Address-of
#           sizeof              Size-of
#           new, new[]          Dynamic memory allocation
#           delete, delete[]    Dynamic memory deallocation
#     4     .* ->*              Pointer to member    Left-to-right
#     5     * / %               Multiplication, division, and remainder
#     6     + -                 Addition and subtraction
#     7     << >>               Bitwise left shift and right shift
#     8     < <=                For relational operators < and <= respectively
#           > >=                For relational operators > and >= respectively
#     9     == !=               For relational = and != respectively
#     10    &                   Bitwise AND
#     11    ^                   Bitwise XOR (exclusive or)
#     12    |                   Bitwise OR (inclusive or)
#     13    &&                  Logical AND
#     14    ||                  Logical OR
#     15    ?:                  Ternary conditional  Right-to-Left
#     16    =                   Direct assignment (provided by default for C++ classes)
#           += -=               Assignment by sum and difference
#           *= /= %=            Assignment by product, quotient, and remainder
#           <<= >>=             Assignment by bitwise left shift and right shift
#           &= ^= |=            Assignment by bitwise AND, XOR, and OR
#     17    throw               Throw operator (exceptions throwing)
#     18    ,                   Comma          Left-to-right

def p_testExpression(p):
    '''testExpression : expression
                      | expression MATCHES expression AS SYMBOL
                      | expression MATCHES_I expression AS SYMBOL
                      '''
    if len(p) <= 2:
        p[0] = p[1]
        return
    p[0] = node.Matches(p[1], p[3], case=p[2] == 'matches', matchName=p[5])


# TODO: split this up into comparison expressions and manipulating expressions
def p_expression_operator(p):
    '''expression : expression EQUAL expression
                  | expression NOTEQUAL expression
                  | expression LESSERTHAN expression
                  | expression LESSEROREQUAL expression
                  | expression GREATERTHAN expression
                  | expression GREATEROREQUAL expression
                  | expression PLUS expression
                  | expression MINUS expression
                  | expression MULTIPLY expression
                  | expression MODULUS expression
                  | expression DIVIDE expression
                  | expression AND expression
                  | expression OR expression
                  | expression BITWISENOT expression
                  | expression BITWISEAND expression
                  | expression BITWISEOR expression
                  | expression BITWISEXOR expression
                  | expression SHIFTLEFT expression
                  | expression SHIFTRIGHT expression
                  '''
    kls = node.Operator.getClassForOperator(p[2])
    # tbd: this should be done for all associative operators... or should it?
    if kls == node.Plus and isinstance(p[1], kls):
        p[0] = p[1]
        p[0].append(p[3])
    else:
        p[0] = kls(p[1], p[3])


def p_expression_has(p):
    '''expression : expression HAS expression
                  | expression HAS_I expression
                  '''
    p[0] = node.Has(p[1], p[3], case=p[2] == 'has')


def p_expression_matches(p):
    '''expression : expression MATCHES expression
                  | expression MATCHES_I expression
                  '''
    p[0] = node.Matches(p[1], p[3], case=p[2] == 'matches')


def p_expression_unary(p):
    '''expression : NOT expression
                  | BITWISENOT expression
                  '''
    p[0] = node.Operator.getClassForOperator(p[1])(p[2])


def p_expression_uminus(p):
    'expression : MINUS expression %prec UMINUS'
    p[0] = -p[2]


def p_expression_factor(p):
    'expression : factor'
    p[0] = p[1]


def p_factor_functioncall(p):
    'factor : functioncall'
    p[0] = p[1]


def p_functioncall(p):
    'functioncall : SYMBOL LPAREN expressionList RPAREN'
    if not re.match('^print(raw|v)?$', p[1]):
        #TODO: check that we are in a function block. Otherwise we will need to wrap in `<esi:vars>`.
        p[0] = node.FunctionCall(p[1], *p[3])
        return
    p[0] = node.Output(*p[3], raw=(p[1] == 'printraw'))
    if p[1].startswith('printv'):
        p[0] = node.Block(
            node.Output('<esi:vars>', raw=True),
            p[0],
            node.Output('</esi:vars>', raw=True))


def p_factor_literal(p):
    'factor : literal'
    p[0] = p[1]


def p_factor_varref(p):
    'factor : SYMBOL'
    p[0] = node.Variable(p[1])


def p_factor_varref_key(p):
    'factor : SYMBOL LBRACKET expression RBRACKET'
    p[0] = node.Variable(p[1], key=p[3])

def p_factor_varref_ternary(p):
    'factor : testExpression QUESTION expression COLON expression'
    iftrue = node.Block(node.Variable(p[1], default=p[4]))
    iffalse = node.Block(node.Variable(p[1], default=p[5]))
    p[0] = node.If(p[1], iftrue, noMatchStatement=iffalse)

def p_factor_varref_default(p):
    'factor : SYMBOL OR expression'
    p[0] = node.Variable(p[1], default=p[3])

def p_factor_varref_key_default(p):
    'factor : SYMBOL LBRACKET expression RBRACKET OR expression'
    p[0] = node.Variable(p[1], key=p[3], default=p[6])

def p_factor_expr(p):
    'factor : LPAREN expression RPAREN'
    p[0] = p[2]


def p_factor_list(p):
    '''factor : LBRACKET listExpressionList RBRACKET
              | LBRACKET listExpressionList COMMA RBRACKET
              '''
    p[0] = node.List(*p[2])


def p_listExpressionList(p):
    '''listExpressionList : empty
                          | listExpression
                          | listExpressionList COMMA listExpression
                          '''
    p[0] = []
    if len(p) > 3:
        p[0] = p[1] + [p[3]]
    elif len(p) > 1 and p[1] is not None:
        p[0].append(p[1])


def p_listExpression(p):
    '''listExpression : expression
                      | rangeExpression
                      '''
    p[0] = p[1]


def p_rangeExpression(p):
    'rangeExpression : expression RANGE expression'
    p[0] = node.Range(p[1], p[3])


def p_expressionList(p):
    '''expressionList : empty
                      | expression
                      | expressionList COMMA expression
                      '''
    p[0] = []
    if len(p) > 3:
        p[0] = p[1] + [p[3]]
    elif len(p) > 1 and p[1] is not None:
        p[0].append(p[1])


def p_factor_dict(p):
    '''factor : LBRACE dictionaryList RBRACE
              | LBRACE dictionaryList COMMA RBRACE
              '''
    p[0] = node.Dictionary(*p[2])


def p_dictionaryList(p):
    '''dictionaryList : empty
                      | dictionaryEntry
                      | dictionaryList COMMA dictionaryEntry
                      '''
    p[0] = []
    if len(p) > 3:
        p[0] = p[1] + [p[3]]
    elif len(p) > 1 and p[1] is not None:
        p[0].append(p[1])


def p_dictionaryEntry(p):
    'dictionaryEntry : literal COLON expression'
    p[0] = (p[1], p[3])


def p_literal(p):
    '''literal : NUMBER
               | stringLiteral
               '''
    p[0] = node.helper.expr(p[1])

    # strings with escaped non printable characters need to be treated with care. ESI doesn't have a means to address
    # this, so we will use a bit of a hack by representing the unprintable characters in base64 and use the decode function
    if 0==1 and isinstance(p[0], node.Literal) and p[0].value and isinstance(p[0].value, str):
        vals = []
        index = 0
        init_literal = p[0].value
        unprintable = re.compile(u'[\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
                                + '\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff]+')
        for match in unprintable.finditer(init_literal):
            text = init_literal[index:match.start()]
            non_text = init_literal[match.start():match.end()]
            index = match.end()
            if text: vals.append(node.Literal(text))
            vals.append(node.FunctionCall("base64_decode", node.Literal(base64.b64encode(non_text.encode('utf-8')).decode('utf-8'))))
        if index < len(init_literal): vals.append(node.Literal(init_literal[index:]))
        if len(vals) == 1:
            p[0] = vals[0]
        elif len(vals) > 1:
            p[0] = node.Add(*vals)


def p_stringLiteral(p):
    '''stringLiteral : STRING
                     | stringLiteral STRING
                     '''
    p[0] = p[1]
    if len(p) > 2:
        p[0] += p[2]


def p_literal_bool(p):
    '''literal : TRUE
               | FALSE
               '''
    p[0] = node.Literal(p[1] == 'true')


# really should only apply to literals...
def p_property_string(p):
    '''expression : property SYMBOL
                    | property SYMBOL OR factor
                    | property SYMBOL LPAREN expression RPAREN
                    | property SYMBOL LPAREN expression RPAREN OR factor
                     '''
    if p[2] == "length":
        p[0] = node.FunctionCall('len', p[1])
    elif p[2] == "indexOf":
        p[0] = node.FunctionCall('index', p[1], p[4])
    elif p[2] == "charAt":
        if isinstance(p[1], node.Variable):
            if p[1].key is None:
                p[1] = p[1].name
            else:
                p.lexer.error(
                    'complex expressions are not supported in ESI. break apart into multiple variable asignments',
                    abort=SyntaxError)

        p[0] = node.Variable(p[1], key=p[4])
        if len(p) >= 7:
            p[0] = node.Variable(p[1], key=p[4], default=p[7])
    elif len(p) == 3:
        p[0] = node.Variable(p[1], key=p[2])
    elif len(p) == 5:
       p[0] = node.Variable(p[1], key=p[2], default=p[4])
    else:
        p.lexer.error('unknown object property: "%s"' % (p[1]), abort=SyntaxError)


# error rule for syntax errors
def p_error(t):
    if t is None:
        # TODO: make this work better...
        # t.lexer.error('unexpected EOF')
        # return
        raise SyntaxError('unexpected EOF')
    t.lexer.error('unexpected parser token "%s"' % (t.value,), lexpos=t.lexpos)

