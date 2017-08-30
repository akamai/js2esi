/**
 * unit testing js functions
 */

function convert(var0) {
  // note: this is an endless loop - but i don't have access to conditionals
  //       until a later unit test!... ;-)
  return convert(15) + convert(var0);
}

function someFunc()
// effects: testing comments
//          before the block-open
{
  return false;
}

// function call with one arg
let result = convert('good');

// empty function call
let ret = someFunc();

// function arguments.... whee! :)
function double( arg ) {
  return arg + arg;
}

function add( arg1, arg2 ) {
  return arg1 + arg2;
}

function del( arg1, arg2 = 0 ) {
  return arg1 - arg2;
}