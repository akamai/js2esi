/**
 * unit testing js expression with NOT ("!")
 */

if ( ! func1() && func2() )
  str = 'first';
else if ( ! ( func1() && func2() ) )
  str = 'second';

