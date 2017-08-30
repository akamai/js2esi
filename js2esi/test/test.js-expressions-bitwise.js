/**
 * unit testing js bitwise and logical expressions
 */

// this is a silly way of doing v & 0xFF...
let v = 1;
v = ( v << 24 ) >> 24; //1
v = v & 255; //1

// this should set var0 to 10...d
v = (1 << 2) | (1 << 4); // == 20

if ( v & ( 1 << 3 ) )
  s = 'third bit set';

// addition, subtraction, multiplication, modulus and division
// TODO: this should collapse to: result = '****** six stars!' instead of '*'*6 + ' six stars';
// TODO: but should we really be able to multiply a scalar by a number?
result = ( '*' * ( ( 25 % 13 ) / ( 3 - 1 ) )  ) + ' six stars!';

// equality, non-equality, lesser/greater comparison, logical AND/OR
if ( a == 12 && ( b != 'options' || c <= 4 ) && d < 5 && e > 15 )
  boolval = e >= 9;

// bitwise xor/not...
value = ( ( 1 << 5 ) | ( 1 << 3 ) ) >> 1; // == 20
value = value ^ ( ~ 10 );
if ( value & 4 )
  match = 'yup!';



