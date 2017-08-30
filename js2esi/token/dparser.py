""" js2esi.token.dparser
ply.yacc parsing definitions for esi-to-js decompilation
"""

import sys
from js2esi.token.dtokens import *
from js2esi.node import helper
from js2esi import node

__author__ = "Phil Grabner, Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"

start = 'script'


def p_empty(p):
    'empty :'
    pass


def p_script(p):
    '''script : nvStatements
              | empty
              | cTRY eTRY eATTEMPT eEXCEPT eCHOOSE eOTHERWISE cEVAL cINCLUDE
              | cBREAK oBREAK eBREAK cCOMMENT cRETURN
              '''
    # TODO: the last two lines are bogus!... (they are to quell the unused token warnings...)
    p[0] = p[1]


def p_nvStatements(p):
    '''nvStatements : nvStatement
                    | nvStatements nvStatement
                    '''
    if not isinstance(p[1], node.Block):
        p[0] = node.Block(p[1])
    else:
        p[0] = p[1]
    if len(p) > 2:
        p[0].append(p[2])


# def p_declarations(p):
#   '''declarations : declaration
#                   | declarations declaration
#                   '''
#   if not isinstance(p[1], node.Block):
#     p[0] = node.Block(p[1])
#   else:
#     p[0] = p[1]
#   if len(p) > 2:
#     p[0].append(p[2])

# def p_declaration(p):
#   '''declaration : statement
#                  | comment
#                  '''
#                  # | function
#   p[0] = p[1]

# def p_statements_multi(p):
#   'statements : statements cstatement'
#   if not isinstance(p[1], node.Block):
#     p[0] = node.Block(p[1])
#   else:
#     p[0] = p[1]
#   p[0].append(p[2])

# def p_statements_mt(p):
#   'statements : empty'
#   p[0] = node.Block(p[1])

# def p_statements_single(p):
#   'statements : cstatement'
#   p[0] = p[1]

# def p_statements_one(p):
#   '''cstatement : comment
#                 | statement
#                 '''
#   p[0] = p[1]

def p_nvStatement(p):
    '''nvStatement : esiStatement
                   | rawString
                   '''
    p[0] = p[1]


def p_rawString(p):
    'rawString : string'
    p[0] = node.Output(p[1])


def p_esiStatement(p):
    '''esiStatement : comment
                    | assign
                    | try
                    | condition
                    | evalinclude
                    | vars
                    | debug
                    | functiondef
                    | return
                    | loop
                    | break
                    '''
    # tbd: "return" and "break" should only be valid within, respectively,
    #      "functiondef" and "loop" contexts...
    p[0] = p[1]


def p_statements(p):
    '''statements : statement
                  | statements statement
                  '''
    if not isinstance(p[1], node.Block):
        p[0] = node.Block(p[1])
    else:
        p[0] = p[1]
    if len(p) > 2:
        p[0].append(p[2])


def p_statement(p):
    '''statement : esiStatement
                 | varsStatement
                 '''
    p[0] = p[1]


def p_varsStatement(p):
    'varsStatement : varsExpr'
    p[0] = node.Output(p[1])


# COMMENTS


def p_comment(p):
    'comment : sCOMMENT aTEXT string xEMPTY'
    p[0] = node.Comment(p[3])


# def p_comment_cont(p):
#   'comment : ESICOMMENT commentcont'
#   lines = [p[1]] + p[2]
#   # strip the largest amount of leading whitespace common to all lines
#   while len(lines[0]) > 0 and lines[0][0].isspace():
#     newlines = [e[1:] for e in lines if len(e) > 0 and e[0] == lines[0][0]]
#     if len(newlines) != len(lines):
#       break
#     lines = newlines
#   p[0] = node.Comment('\n'.join(lines))

# def p_commentcont_multi(p):
#   'commentcont : commentcont ESICOMMENT_CONT'
#   p[0] = p[1] + [p[2]]

# def p_commentcont(p):
#   'commentcont : ESICOMMENT_CONT'
#   p[0] = [p[1]]


# ASSIGNMENT


def p_assign(p):
    '''assign : sASSIGN aNAME assignName aVALUE attrExpression xEMPTY
              | sASSIGN aNAME assignName xEND expression cASSIGN
              '''
    p[0] = node.Assign(p[3][0], p[5], key=p[3][1])


def p_assignName(p):
    '''assignName : SYMBOL
                  | SYMBOL LBRACE expression RBRACE
                  '''
    p[0] = (p[1], len(p) > 3 and p[3] or None)


# CONDITIONALS


def p_condition(p):
    'condition : oCHOOSE whenClauseList ws otherwiseClause ws cCHOOSE'
    ret = p[4]
    for when in reversed(p[2]):
        ret = node.If(when[0], when[1], ret)
        if when[2] is not None:
            ret.setMatchName(when[2])
    p[0] = ret


def p_whenClauseList(p):
    '''whenClauseList : iws
                      | whenClause
                      | whenClauseList whenClause
                      '''
    p[0] = []
    if len(p) > 2:
        if p[2] is None:
            p[0] = p[1]
        else:
            p[0] = p[1] + [p[2]]
    elif len(p) > 1 and p[1] is not None:
        p[0].append(p[1])


def p_whenClause_mt(p):
    'whenClause : sWHEN aTEST expression xEND cWHEN'
    p[0] = (p[3], None, None)


def p_whenClause(p):
    'whenClause : sWHEN aTEST expression xEND statements cWHEN'
    p[0] = (p[3], p[5], None)


def p_whenClause_matchname(p):
    'whenClause : sWHEN aTEST expression aMATCHNAME string xEND statements cWHEN'
    p[0] = (p[3], p[7], p[5])


def p_otherwiseClause(p):
    '''otherwiseClause : empty
                       | oOTHERWISE statements cOTHERWISE
                       '''
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = p[1]


# TRY BLOCKS


def p_try(p):
    'try : oTRY oATTEMPT statements cATTEMPT cTRY'
    p[0] = node.Try(p[3])


def p_tryexcept(p):
    'try : oTRY oATTEMPT statements cATTEMPT oEXCEPT statements cEXCEPT cTRY'
    p[0] = node.Try(p[3], p[6])


# EVAL/INCLUDE


includeParamMap = {
    'onerror': 'onError',
    'maxwait': 'maxWait',
    'no-store': 'noStore',
    'appendheader': 'appendHeader',
    'removeheader': 'removeHeader',
    'setheader': 'setHeader',
}


def p_evalinclude(p):
    '''evalinclude : sINCLUDE includeAttributes xEMPTY
                   | sEVAL includeAttributes xEMPTY
                   '''
    kls = p[1] == 'eval' and node.Eval or node.Include
    args = dict()
    for k, v in p[2]:
        if k in includeParamMap:
            k = includeParamMap[k]
        if not k.endswith('Header'):
            args[k] = v
            continue
        if not k in args:
            args[k] = []
        args[k].append(v)
    if 'src' not in args:
        p.lexer.error('"esi:%s" requires attribute "src"' % (p[1],), lexpos=p.lexspan(1)[0], abort=SyntaxError)
    arglist = kls.getInitParameterList()
    for k in args.keys():
        if k not in arglist:
            argmap = dict([(e.lower(), e) for e in arglist])
            dym = ''
            if k.lower() in argmap:
                dym = ' - did you mean "%s"?' % (argmap[k],)
            p.lexer.error('"esi:%s" does not accept attribute "%s"%s' % (p[1], k, dym), abort=SyntaxError)
    p[0] = kls(**args)


def p_includeAttributes(p):
    '''includeAttributes : empty
                         | includeAttribute
                         | includeAttributes includeAttribute
                         '''
    p[0] = []
    if len(p) > 2:
        p[0] = p[1] + [p[2]]
    elif len(p) > 1 and p[1] is not None:
        p[0].append(p[1])


def p_includeAttribute(p):
    '''includeAttribute : aSRC varsExpr
                        | aALT varsExpr
                        | aDCA varsExpr
                        | aONERROR varsExpr
                        | aMAXWAIT varsExpr
                        | aTTL varsExpr
                        | aNOSTORE varsExpr
                        | aAPPENDHEADER varsExpr
                        | aREMOVEHEADER varsExpr
                        | aSETHEADER varsExpr
                        | aMETHOD varsExpr
                        | aENTITY varsExpr
                        '''
    p[0] = (p[1], p[2])
    # tbd: this is a serious hack... but, then again, so is ESI...
    if p[1] == 'dca' and isinstance(p[2], node.Literal) and '\'' in p[2].value:
        p[0] = (p[1], node.Literal(p[2].value.replace('\'', '')))
    # tbd: this is somewhat of a hack as well... it indicates that
    #      includeAttribute should probably not be a varsExpr, but something
    #      a little smarter...
    if p[1] == 'maxwait' and isinstance(p[2], node.Literal):
        p[0] = (p[1], node.Literal(int(p[2].value)))


# VARS


def p_vars_inline(p):
    'vars : sVARS aNAME assignName xEMPTY'
    p[0] = node.Output(node.Variable(p[3][0], key=p[3][1]), vars=True)


def p_vars_block(p):
    'vars : sVARS xEND varsExpr cVARS'
    if p[3] is not None:
        p[0] = node.Output(p[3], vars=True)


def p_vars_mixed(p):
    'vars : sVARS xEND statements cVARS'
    if p[3] is not None:
        p[0] = node.Block(
            node.Output('<esi:vars>', raw=True),
            p[3],
            node.Output('</esi:vars>', raw=True),
        )


# LOOPS


def p_loop_noitem(p):
    'loop : sFOREACH aCOLLECTION expression xEND statements cFOREACH'
    p[0] = node.ForEach(p[3], p[5])


def p_loop_item0(p):
    'loop : sFOREACH aITEM SYMBOL aCOLLECTION expression xEND statements cFOREACH'
    p[0] = node.ForEach(p[5], p[7], key=p[3])


def p_loop_item1(p):
    'loop : sFOREACH aCOLLECTION expression aITEM SYMBOL xEND statements cFOREACH'
    p[0] = node.ForEach(p[3], p[7], key=p[5])


def p_break(p):
    'break : eBREAK'
    p[0] = node.Break()


# FUNCTION DECLARATIONS


def p_functiondef(p):
    # tbd: it would be *great* if i could specify that only statements within
    #      this context could include the return statement...
    'functiondef : sFUNCTION aNAME SYMBOL xEND statements cFUNCTION'
    # tbd: it would be *great* to detect any 'var# = ARGS[#];' statements
    #      and convert them into proper parameters...
    p[0] = node.FunctionDefinition(p[3], [], p[5])


def p_return(p):
    'return : sRETURN aVALUE attrExpression xEMPTY'
    p[0] = node.FunctionReturn(p[3])


# def p_return_empty(p):
#   'return : eRETURN'
#   p[0] = node.FunctionReturn()


# DEBUG


def p_debug(p):
    '''debug : eDEBUG
             | oDEBUG cDEBUG
             '''
    p[0] = node.Output('<esi:debug/>', raw=True, vars=False)


# GENERICS


def p_attrExpression(p):
    'attrExpression : expression'
    p[0] = p[1]


def p_varsExpr(p):
    '''varsExpr : empty
                | varsExprElement
                | varsExpr varsExprElement
                '''
    if p[1] is None:
        return
    if len(p) <= 2:
        p[0] = p[1]
    else:
        if isinstance(p[1], node.Plus):
            p[0] = p[1]
            p[0].append(p[2])
        else:
            p[0] = node.Plus(p[1], p[2])


def p_varsExpr_literal(p):
    'varsExprElement : string'
    p[0] = node.Literal(p[1])


def p_varsExpr_varref(p):
    'varsExprElement : VARREF'
    p[0] = node.Variable(p[1])


def p_varsExpr_functioncall(p):
    'varsExprElement : functioncall'
    p[0] = p[1]


def p_varsExpr_varref_more(p):
    'varsExprElement : VARREF varKey varDefault RPAREN'
    p[0] = node.Variable(p[1], key=p[2], default=p[3])


def p_varKey(p):
    '''varKey : empty
              | LBRACE expression RBRACE
              '''
    if len(p) > 2:
        p[0] = p[2]


def p_varDefault(p):
    '''varDefault : empty
                  | PIPE expression
                  '''
    if len(p) > 2:
        p[0] = p[2]


def p_ws(p):
    '''ws : empty
          | WS
          '''
    p[0] = p[1]


def p_iws(p):
    'iws : ws'
    p[0] = None


# EXPRESSIONS


precedence = (
    # lowest to highest precedence rules:
    # TODO: all this needs to be confirmed
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'BITWISEOR', 'PIPE'),
    ('left', 'BITWISEXOR'),
    ('left', 'BITWISEAND'),
    ('nonassoc', 'EQUAL', 'NOTEQUAL', 'LESSERTHAN', 'LESSEROREQUAL', 'GREATERTHAN', 'GREATEROREQUAL',
     # 'HAS', 'HAS_I', 'MATCHES', 'MATCHES_I'
     ),
    # tbd: confirm that NOT is lower than the others... (usually it isn't)
    ('nonassoc', 'NOT', 'BITWISENOT'),

    ('left', 'SHIFTLEFT', 'SHIFTRIGHT'),

    # tbd: confirm that ESI operators *%/ do not have higher precedence than +-, eg:
    #   ('left', 'PLUS', 'MINUS'),
    #   ('left', 'MULTIPLY', 'MODULUS', 'DIVIDE'),
    ('left', 'PLUS', 'MINUS', 'MULTIPLY', 'MODULUS', 'DIVIDE'),

    ('right', 'UMINUS'),
)


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
                  | expression PIPE expression
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
    'functioncall : DOLLAR SYMBOL LPAREN expressionList RPAREN'
    p[0] = node.FunctionCall(p[2], *p[4])


def p_functioncall_tokenized(p):
    'functioncall : FUNCCALL expressionList RPAREN'
    p[0] = node.FunctionCall(p[1], *p[2])


def p_factor_varref(p):
    'factor : DOLLAR LPAREN SYMBOL varrefKey varrefDefault RPAREN'
    p[0] = node.Variable(p[3], key=p[4], default=p[5])


def p_varrefKey(p):
    '''varrefKey : empty
                 | LBRACE expression RBRACE
                 '''
    if len(p) > 2:
        p[0] = p[2]


def p_varrefDefault(p):
    '''varrefDefault : empty
                     | BITWISEOR literal
                     | PIPE literal
                     '''
    p[0] = None
    if len(p) > 2:
        # p[0] = node.Literal(p[2])
        # tbd: why does node.Variable's "default" init parameter require a string?...
        p[0] = p[2]


def p_factor_literal(p):
    'factor : literal'
    p[0] = p[1]


def p_factor_symbol(p):
    'factor : SYMBOL'
    p[0] = node.Literal(p[1])


def p_factor_expr(p):
    'factor : LPAREN expression RPAREN'
    p[0] = p[2]


def p_factor_list(p):
    'factor : LBRACKET listExpressionList RBRACKET'
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
    'factor : LBRACE dictionaryList RBRACE'
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


def p_dictionaryEntry_symbol(p):
    'dictionaryEntry : SYMBOL COLON expression'
    p[0] = (node.Literal(p[1]), p[3])


def p_literal(p):
    '''literal : NUMBER
               | string
               '''
    p[0] = node.Literal(p[1])


def p_string(p):
    '''string : WS
              | STRING
              | string WS
              | string STRING
              '''
    p[0] = p[1]
    if len(p) > 2:
        p[0] += p[2]


# ERROR HANDLING


# error rule for syntax errors
def p_error(t):
    if t is None:
        # TODO: make this work better...
        # t.lexer.error('unexpected EOF')
        # return
        raise SyntaxError('unexpected EOF')
    t.lexer.error('unexpected parser %s token: "%s"' % (t.type, t.value), lexpos=t.lexpos)

