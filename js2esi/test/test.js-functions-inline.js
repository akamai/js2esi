/**
 * unit testing inlining of js functions
 */
function multiply(a, b)
{
  "inline";
  return a * b;
}

function times(a, b)
{
    return multiply(a, b);
}

function double(a)
{
  "inline";
  return multiply(a, 2);
}

function x2(a)
{
  return times(a, 2);
}

sixteen = multiply(4, double(2));

if ( multiply(3, sixteen) == double(24) )
  match = 'true';

/**
 * TODO: inline needs to be extended to support inlining beyond just one-line
 *      expressions. note that this brings many complications... such as:
 *        - passing subkey variable references
 *        - parameter defaulting
 *        - variable defaulting
 *      actually, most of these apply no matter what...
 *      so here is the non-expr inlining that would be great:
 */

// function inline dmsg(msg, level=0)
// {
//   if ( level <= 0 )
//     pfx = '[  ] ';
//   else if ( level <= 30 )
//     pfx = '[--] ';
//   else
//     pfx = '[**] ';
//   dbg = dbg + pfx + msg + '\n';
// }
// dbg = 'debug line 1\n';
// dmsg('debug line 2');

