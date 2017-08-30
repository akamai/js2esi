# JS to ESI compiler and decompiler (`js2esi`, `esi2js`)
Convert Javascript to from from ESI (Edge Side Includes). Write javascript code that will compile to ESI and run at the Edge.

## Synopsis

```
js2esi | esi2js
[--version] [-h|--help] [-v|--verbose]
[-l|--lex] [-n|--node] [-d|--decompile]
[-w|--no-warning] [-L|--library PATH] [-O|--optimize LEVEL]
[-o|--output FILENAME]
{FILENAME|-}
```

## Overview

`js2esi` is a tool that can compile js 'lite' into Edge Side Includes (ESI) using the compiler of the same name, js. The language is, at it's core, nothing more than syntactic sugar to make ESI coding simpler. As a result, it is limited to the exact same constraints as ESI is. It does, however, also provide some more advanced features, such as modularization and inlining, that get resolved during compilation. The js dev must always be aware that js is converted to ESI, be aware of those limitations, and review the resulting ESI to ensure compatibility and correctness.

## Getting started (dev)

The simplist way to get started is to: 
1. clone the repo
2. run `./dev.sh` to get all the dependencies installed, etc
3. `. venv/bin/activate` to activate your local environment
4. run `js2esi` as below

Test coverage uses Nose. Just run `nosetests`  


## The `js2esi` Program

The program can be used to compile js files to ESI as well as the reverse, decompile ESI to js. The program accepts the following options:

### Options

`--version` 
Display program version identifier and exit.

`-h | --help`
Display command options and exit.

`-v | --verbose`
Enable verbose output (multiple invocations increase verbosity).

`-l | --lex`
Display lexical parsing tokens - primarily useful if js2esi is having trouble parsing your source file.

`-n | --node`
Display the Node representational form instead of the js or ESI output (primarily useful for js2esi debugging).

`-d | --decompile`
Enable ESI-to-js decompilation instead of js-to-ESI compilation. Note that this is implied if invoked as esi2js command (they are symbolic links to each other).

`-w | --no-warning`
By default, the ESI output includes a warning that the ESI was generated as output from js2esi. This option disables the warning.

`-L PATH | --library PATH`
Add the specified PATH to the js2esi module lookup path (for resolving "import" statements). The path will be append to any paths already provided by the JSLIB environment variable (see below). The option can be invoked multiple times to append multiple paths.

`-O LEVEL | --optimize LEVEL`
Set the code optimization level to LEVEL, which can range from 0 (no optimizations) to 9 (maximum optimizations). The default value, 7, is safe and will only apply non-destructive optimizations; levels above 7 should be reserved for ESI scripts that are completely independent/standalone — i.e. the script does not use, or is not used by, any eval statements that may depend on variables and functions exposed by this script. This is because variables/functions will be removed if unused and/or may be renamed to be more efficient.

`-o FILENAME | --output FILENAME`
output the compiled code to FILENAME. Defaults to STDOUT

`FILENAME | -`
Specifies the FILENAME that should be processed. If - is specified instead of the path to a filename, then STDIN will be used.

### Environment

The js2esi program is sensitive to the following environmental variables:

`JSLIB` This is a colon (":") delimited list of path names, similar to $PATH, that will be used to find any external js source referenced by import statements.

### Installation

The js2esi program and library are distributed as python eggs. To install the egg, you first need to install Python (3.5 or later) and setuptools (0.6 or later) — note that on most Unix systems, these will already be installed. Once they are, the program "easy_install" will be available at your prompt, and — as the name implies — all you need to do to install js2esi is:

```sh
$ git clone 
$ ./dev.sh
```

### Example

```sh
$ cat sample.js
# this is a sample js file.
myvar = 'http://'.length + HTTP_HOST.length + len(REQUEST_PATH);

$ js2esi -w sample.js
<esi:assign name="myvar" value="$len('http://')+$len($(HTTP_HOST))+$len($(REQUEST_PATH))"/>
```

## Javascript 'like' language

The lexical parser is intended to be javascript compatible. However, it isn't very sophisticaed because of some of the underlying limitations of ESI. 

The following syntax guide shows how to construct js code that compile nicely to ESI.

> #### Important
> Please read the [section called “Todo List”](), as several things that you may expect to work don't. Also take a look at the [section called “Known Bugs”](#knownbugs) (surprise!).

Some general rules in the syntax of js:

* Whitespace is irrelevant — except in literals, it will be ignored completely.
* The "if/else" construct is ONLY a "choose/when" shorthand, and must therefore be used appropriately and leverage the "else if" construct when possible.

Some general js limitations due to limitations in ESI:

* All ESI limitations apply! Including, but not limited to: total script size, recursion, variable size and inclusion limits.
* The js constants "true" and "false" are represented as the ESI integers 1 and 0 - although this works as expected when evaluated in boolean context, it may behave slightly differently in non-boolean contexts.
* Doing string indexing is faster than dictionary lookups — avoid dictionary lookups.

Currently, the method to get the compiled js to output content (i.e. to get ESI to output content) is a bit of a "workaround". Several reserved functions exist for this purpose: print(), printv() and printraw() (see Example 9, “Composing Output”).

js2esi supports one nifty thing that ESI does not: inlining either external or internal code. This feature is activated with the import function call and the inline keyword. The difference between importing and including/eval'ing is synonymous to static versus dynamic linking: importing will pull the external code in during js2esi compilation, whereas including/eval'ing will do so during ESI execution. Please see Example 12, “Imports” and Example 5, “Inlined Functions” for details.

### Examples:

* [Example 1, “Comments”](#example1)
* [Example 2, “Variable Assignments”](#example2)
* [Example 3, “Operators”](#example3)
* [Example 4, “Function Declarations and Calls”](#example4)
* [Example 5, “Inlined Functions”](#example5)
* [Example 6, “Conditional Statements”](#example6)
* [Example 7, “Match Operator”](#example7)
* [Example 8, “For Of”](#example8)
* [Example 9, “For Loops”](#example8)
* [Example 10, “Composing Output”](#example9)
* [Example 11, “Try/Catch Blocks”](#example10)
* [Example 12, “Include and Eval Statements”](#example11)
* [Example 13, “modules”](#example12)

### Example 1. Comments

js input:

```
/** anything after a hash symbol ('#') will be regarded as a comment and
 * stripped out completely, with the exception of a comment that begins
 * with a triple hash, which will be converted into an ESI comment, eg.
 */
//### this ESI code is generated -- do not edit manually
// the above will appear in the output, but nothing else
```

ESI output:

```
<esi:comment text="this ESI code is generated -- do not edit manually"/>
```

### Example 2. Variable Assignments

js2esi supports all of the data structures that ESI does, as well as a few additional unary assignment operators. Note that, just like in ESI, it is possible to reference a variable without using or declaring it.

js input:

```
varName = 'someString';
numVal  = 919;
boolVal = true;
boolVal = false;
array   = [ 'firstVal', 2, [ 'subarray', 'el', ] ];
hash    = { 'foo': 'this', 'bar': 'that', };
varName += ' - and the rest';
numVal  -= 10;
numVal  *= 5;
numVal  /= 5;
numVal  %= 5;
numVal  ++;
numVal  --;

# variable referencing with default values can also be done:

value   = hash['bar'] | 'none';
```

ESI output:

```
<!-- NOTE: newlines/whitespace added for clarity - not normally in js2esi output -->
<esi:assign name="varName" value="'someString'"/>
<esi:assign name="numVal" value="919"/>
<esi:assign name="boolVal" value="1"/>
<esi:assign name="boolVal" value="0"/>
<esi:assign name="array" value="['firstVal',2,['subarray','el']]"/>
<esi:assign name="hash" value="{'foo':'this','bar':'that'}"/>
<esi:assign name="varName" value="$(varName)+' - and the rest'"/>
<esi:assign name="numVal" value="$(numVal)-10"/>
<esi:assign name="numVal" value="$(numVal)*5"/>
<esi:assign name="numVal" value="$(numVal)/5"/>
<esi:assign name="numVal" value="$(numVal)%5"/>
<esi:assign name="numVal" value="$(numVal)+1"/>
<esi:assign name="numVal" value="$(numVal)-1"/>
<esi:assign name="value" value="$(hash{'bar'}|'none')"/>
```

### Example 3. Operators

Most commonly used operators are supported, including bitwise shifting and AND/OR. Note that if you use bitwise AND/OR, bitwise ESI will be generated — but this will only work if legacy bitwise operators are disabled (on Akamai, this means setting the `<edgecomputing:esi.legacy-logical-operators>` tag to `off`, which by default is `on`). The js2esi optimizer is able to detect certain operations with literals (i.e. hard-coded values) that can be evaluated at compile time, and thus yield more efficient ESI code.

js input:

```
# addition, subtraction, multiplication, modulus and division
result = ( '*' * ( ( 25 % 13 ) / ( 3 - 1 ) )  ) + ' six stars!';

# equality, non-equality, lesser/greater comparison, logical AND/OR
if ( a == 12 && ( b != 'options' || c <= 4 ) && d < 5 && e > 15 )
  boolval = e >= 9;

# bitwise AND/OR/XOR, bitwise shifting
value = ( ( 1 << 5 ) | ( 1 << 3 ) ) >> 1; # == 10
value = value ^ ( ~ 10 );
if ( value & 4 )
  match = 'yup!';
```

ESI output:

```
<!-- NOTE: newlines/whitespace added for clarity - not normally in js2esi output -->
<esi:assign name="result" value="('*'*6)+' six stars!'"/>
<esi:choose>
  <esi:when test="((($(a)==12) && (($(b)!='options') || ($(c)<=4))) && ($(d)<5)) && ($(e)>15)">
    <esi:assign name="boolval" value="$(e) >= 9"/>
  </esi:when>
</esi:choose>
<esi:assign name="value" value="((1<<5) | (1<<3)) >> 1"/>
<esi:assign name="value" value="$(value) ^ (~ 10)"/>
<esi:choose>
  <esi:when test="$(value) & 4">
    <esi:assign name="match" value="'yup!'"/>
  </esi:when>
</esi:choose>
```

### Example 4. Function Declarations and Calls

js input:

```
function functionName() {
  // all ESI function-scope variables exist in js as well:
  var0 = ARGS[0];
  // here this function will now recursively call itself
  return functionName( var0 );
}

// js allows some nifty function parameter shortcutting:
function func( arg, param = 'default' ) {
  return arg + param;
}
```

ESI output:

```
<!-- NOTE: newlines/whitespace added for clarity - not normally in js output -->
<esi:function name="functionName">
  <esi:assign name="var0" value="$(ARGS{0})"/>
  <esi:return value="$functionName($(var0))"/>
</esi:function>
<esi:function name="func">
  <esi:assign name="arg" value="$(ARGS{0})"/>
  <esi:assign name="param" value="$(ARGS{1}|'default')"/>
  <esi:return value="$(arg)+$(param)"/>
</esi:function>
```

### Example 5. Inlined Functions

js input:

```
function multiply(a, b) {
  "inline";
  return a * b;
}

function squared(value) {
  "inline";
  return multiply(value, value);
}

# js will actually be able to expand the following to a literal result:
four = squared(2);

# but not in the following situation (a later improvement to js may):
sixteen = squared(multiply(four, 1));

# another example
slen = multiply(len(sixteen), 2);
```

ESI output:

```
<!-- NOTE: newlines/whitespace added for clarity - not normally in js output -->
<esi:assign name="four" value="4"/>
<esi:assign name="sixteen" value="($(four)*1)*($(four)*1)"/>
<esi:assign name="slen" value="$len($(sixteen))*2"/>
```

Note that, in the current implementation, there are many restrictions on inlined functions and their invocations:

* Inlined functions may ONLY be called from within expression context, such as when setting and testing variables, returning a value from a function and iterating over a collection.
* Inlined functions MUST NOT contain anything except a return statement.
* Inlined functions MUST NOT be recursive.
* Inlined function call arguments may ONLY be literals, function calls and simple variables (i.e. no variables with sub-keys or defaults).

### Example 6. Conditional Statements

js input:
```
if ( ! isPrinted() && exists( buck )  ) {
  // NOTE: the parens are required after the negation (otherwise it
  //       applies to variable "buck", not the "has")
  if ( ! ( buck has 'muchBlame' ) )
    var = passBuck( buck );
  else
    var = callPrinter();
}
else if ( ! isPrinted() )
  var = callPrinter();
else
  job = nextJob();
```

ESI output:

```
<!-- NOTE: newlines/whitespace added for clarity - not normally in js2esi output -->
<esi:choose>
  <esi:when test="(!$isPrinted()) && $exists($(buck))">
    <esi:choose>
      <esi:when test="!($(buck) has 'muchBlame')">
        <esi:assign name="var" value="$passBuck($(buck))"/>
      </esi:when>
      <esi:otherwise>
        <esi:assign name="var" value="$callPrinter()"/>
      </esi:otherwise>
    </esi:choose>
  </esi:when>
  <esi:when test="!$isPrinted()">
    <esi:assign name="var" value="$callPrinter()"/>
  </esi:when>
  <esi:otherwise>
    <esi:assign name="job" value="$nextJob()"/>
  </esi:otherwise>
</esi:choose>
```

### Example 7. Match Operator

js input:

```
// notes:
//   - the "as ..." is optional
//   - the "matches" and "matches_i" with the optional "as ..."
//     variation can also be used with "choose { when ( ... ) {} }" clauses

if ( myString matches_i '^preamble:([a-z0-9]*):trailer$' as mset ) {
  var = mset[1];
}
```

ESI output:

```
<!-- NOTE: newlines/whitespace added for clarity - not normally in js2esi output -->
<esi:choose>
  <esi:when test="$(myString) matches_i '^preamble:([a-z0-9]*):trailer$'" matchname="mset">
    <esi:assign name="var" value="$(mset{1})"/>
  </esi:when>
</esi:choose>
```

### Example 8. For Of
js input:

```
let values = [0..31]
ret = 0;
for(const item of values) {
  ret += assertOnePlus( item_index, item_number );
  if ( ret > 365 )
    break;
}
```

ESI output:

```
<esi:assign name="values" value="[0..31]"/>
<esi:assign name="ret" value="0"/>
<esi:foreach collection="$(values)">
  <esi:assign name="ret" value="$(ret)+$assertOnePlus($(item_index),$(item_number))"/>
  <esi:choose>
    <esi:when test="$(ret) > 365">
      <esi:break/>
    </esi:when>
  </esi:choose>
</esi:foreach>
```

### Example 9. For loop
js input:

```
ret = 0;
for(let i=0; i <=31; i++) {
  ret += i*i;
}
```

ESI output:

```
<esi:assign name="ret" value="0"/>
<esi:assign name="i" value="0"/>
<esi:assign name="values" value="[0..31]"/>
<esi:foreach collection="$(values)">
  <esi:choose>
    <esi:when test="!($(i) <= 31)">
      <esi:break/>
    </esi:when>
  </esi:choose>
  <esi:assign name="ret" value="$(ret) + ($(i) * $(i))"/>
  <esi:assign name="i" value="$(i)+1"/>
</esi:foreach>
```


### Example 10. Composing Output

js input:

```
printraw( '<esi:vars>\n' );
print( 'only strings, variables and function calls inside a print(): '
       + num2str( 12 + 88 ) + '\n' );
print( myvar );
print( 'no newline here:' );
print( 'foo' + output + '\n' );
printraw( '</esi:vars>' );

// the printraw() function only accepts strings as arguments, and
// outputs them without any escaping. this means that it is possible
// to output ESI with printraw(), whereas print() would have escaped
// them.
//
// the printv() is equivalent to print(), except that the output is
// automatically bracketed by <esi:vars> and </esi:vars>.
// e.g. the following:
//
//   printv( 'quickly print out a var: ' + myString + '!' );
//
// is equivalent to:
//
//   printraw( '<esi:vars>' );
//   print( 'quickly print out a var: ' + myString + '!' );
//   printraw( '</esi:vars>' );
//
```

ESI output:

```
<esi:vars>
only strings, variables and function calls inside a print(): $num2str(100)
$(myvar)no newline here:foo$(output)
</esi:vars>
```

### Example 11. Try/Catch Blocks

js input:

```
try {
  callDangerousFunction( REQUEST_PATH );
}
catch(e) {
  // the object `e` doesn't actually exist in ESI and so it really can't be used in js
  print( '<b>Sorry, that service is currently unavailable.</b>' );
}
```

ESI output:

```
<esi:try>
  <esi:attempt>
    $callDangerousFunction($(REQUEST_PATH))
  </esi:attempt>
  <esi:except>
    <b>Sorry, that service is currently unavailable.</b>
  </esi:except>
</esi:try>
```

### Example 12. Include and Eval Statements

js input:

```
try {
  eval( src='/path/to/include.esi', dca='akamaizer->esi' );
}
catche(e) {
  include( src='/path/to/errorComponent.html' );
}
```

ESI output:

```
<!-- NOTE: newlines/whitespace added for clarity - not normally in js2esi output -->
<esi:try>
  <esi:attempt>
    <esi:eval src="/path/to/include.esi" dca="'akamaizer->esi'"/>
  </esi:attempt>
  <esi:except>
    <esi:include src="/path/to/errorComponent.html"/>
  </esi:except>
</esi:try>
```

### Example 13. modules

external js file "include/js/math/multiply.js":

```
function multiply() {
  return ARGS[0] * ARGS[1];
}
```

js input (with environmental variable JSLIB set to "include/js"):

```
require('math/multiply.js');
myval = multiply( 3, 5 );
```

ESI output:

```
<!-- NOTE: newlines/whitespace added for clarity - not normally in js output -->
<esi:function name="multiply">
  <esi:return value="$(ARGS{0})*$(ARGS{1})"/>
</esi:function>
<esi:assign name="myval" value="$multiply(3,5)"/>
```

The require() function will, by default, only import an external file the first time it is imported. This behaviour can be overriden by setting the "force" named parameter to true, for example:

```
require('math/multiply.js', force=true);
```

## TODO List

Some things that are not yet supported, but eventually will be:

* `<esi:remove> ... </esi:remove>`
* `<esi:text> ... </esi:text>`
* `<!--esi ... -->`

* add support for `'''` string types in ESI... eg:
    `<esi:when test="$(stream_content) matches '''\.wmv$'''">`

* detect functions that don't need a print statement when going ESI-to-js... eg:
    ` <esi:when>$add_header(...)</esi:when>`
  ==>
    `print(add_header(...));`
  * or, generally speaking, standalone functions should be understood as being `printed`?...

* add "in" operator to js, eg:
    input: 
    
    ```
    if ( var in ['a', 'b', 'c'] )
    ```
 
    output: 

    ```
    <esi:when test="$(var)=='a'||$(var)=='b'||$(var)=='c'">
    ```
 
* do functional analysis & error/warnings, including:
  * using variables before they are set (except pre-defined vars).
    this must be a warning, because it is possible for a variable to
    be defined in metadata... note that if the reference is to the
    "value" key in the undefined variable, then it is likely to be
    a metadata variable and should be ignored.
  * calling functions without being in an ESI block, such as `esi:vars`
  * printing variables without being in an ESI block, such as `esi:vars`
* add support for ESI triple-quote quoting mechanism.
* add support for "importing" and "inlining" external modules
* add support for "inlined" functions, eg:

    ```
    function inline dmsg(msg)
    {
      dbg = dbg + msg + '\n';
    }
    dbg = 'debug line 1\n';
    dmsg('debug line 2');
    ```
    
  would get expanded to:

    ```
    dbg = 'debug line 1\n';
    dbg = dbg + 'debug line 2' + '\n';
    ```

  inlining can happen in two contexts:
  
    1. block-context, as is the above context. this is the "simpler"
       context, as in, it has fewer constraints, but it does mean
       that more code needs to be written to be able to handle
       variable substitution and expansion...
    2. expression-context, where the result of the function is being
       used in an expression, such as:
         * `<esi:assign ... name="VARNAME{$HERE()}" ... />`
         * `<esi:assign ... value="$HERE()" ... />`
         * `<esi:when test="$HERE()">`
         * `<esi:return value="$HERE()"/>`
         * `<esi:(eval|include) ... src="$HERE()" ... />`   //this is more of a "vars" context...
         * `<esi:foreach ... collection="$HERE()" ... />`

    
* it would be great to support expressions in print*() statements, eg:

	```
     printv('foo', varName * 3, 'bar');
	```

  esi:
  
	```
    <esi:assign name="ast_tmp_128378" "$(varName)*3"/>
    <esi:vars>foo$(ast_tmp_128378)bar</esi:vars>
	```

* during decompiling, should unknown ESI tags cause an error instead of being converted to print() statements?
* regarding requires:
    * it would be nice if requires tracked what had already been inlined.
    and if an import needed to be imported multiple times, then it
    would have to state that explicitly. for example:
      `require( '/path/to/file.js', allowMultiple='True' );`
    * now that i think about it though, it makes more sense for the imported
    object *itself* to know whether or not it is idempotent. therefore,
    it might be interesting to have something along the `#define` and
    `#ifdef`... or maybe a little simpler, eg:
      `i_am_idempotent();`
* implement unit testing of the docs, too... ie. it should pull out all
  examples, do js=>node and esi=>node, and compare the result...
* non-perfect collapse:

    ```
    dbg += nl + 'Am value is: ' + int(QUERY_STRING['am']);
    ```
    
  went to:  
  
	```  
    <esi:assign name="dbg" value="$(dbg)+($(nl)+'Am value is: '+$int($(QUERY_STRING{am})))"/>
    ```
    
  instead of:

    ```
    <esi:assign name="dbg" value="$(dbg)+$(nl)+'Am value is: '+$int($(QUERY_STRING{am}))"/>
    ```
    
## Known Bugs

There are some known problems:

* Although js supports escaping any character with a backslash (including quotes, double quotes, newlines and backslashes) these are not always correctly escaped when converted to ESI.
* Some of the parameters to `<esi:include>` and `<esi:eval>` don't get converted correctly... no workaround currently.
