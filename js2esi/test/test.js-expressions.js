/**
 * unit testing expressions (precedence, grouping, etc)
 */

let v = 1 + 2 * 3;
v = ( 1 + 2 ) * 3;
v = 1 + -2;
v = 1 + 2 + 3;
v = (1 + 2) + 3;
v = 1 + (2 + 3);
v = 1 + 2 + 3 * 4;
v = ( 1 + 2 + 3 ) * 4;

//TODO:
//v = 0||1;
//v = ( 0 == 1) ? 1 : 2;