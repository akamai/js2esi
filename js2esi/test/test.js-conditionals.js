/**
 * unit testing js conditionals
 */

// declare variables (in case js adds something like "use strict;"...)
let var1 = 'init';
let v = 16;

// test else if
if (len(v) == 16) {
    var1 = 'sixteen';
}
else if (len(v) < 16) {
    var1 = 'lessthan-16';
}
else {
    var1 = 'big';
}


// test if-then
var1 = 're-init';

// TODO: triple-quoting should be conditionally used here...
// TODO:   ie. '^17$' --> '''^17$'''
if (v matches '17'){
    var1 = 'seventeen';
}


// test negation unary operator
if (!v matches '17')
    var1 = 'not-seventeen-false-positive (BUGGY-programming-style)';

// these two are very different
if (!( v matches '17') )
    var1 = 'not-seventeen (good-programming-style)';

// test if-then-else
var1 = 're-re-init';

if (v != 20) {
    var1 = 'not-twenty';
}
else {
    var1 = 'TWENTY IS THE NUMBER!';
}


// test matches ... as
if (v matches_i 'thi.*[str]*ing' as mset) {
    var1 = mset[2];
}

if (v == 20) {
}
else if (v matches 'some.*other.*string' as mset2){
    var1 = mset2[0];
}


// test compounds
if ((v has 'foo') ||(v has_i 'bar') )
    var1 = 'parenScopingOk!';


// weird placed comment
if (v == 'True')
// this comment should just be ignored...
    var1 = 'do_something';

