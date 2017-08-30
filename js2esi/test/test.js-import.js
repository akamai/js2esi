/**
 * test the "require" statement.
 */

require( './moddir/str2int.js' );

//### import a second time (no force)
require( './moddir/str2int.js' );

//### import a third time, this time forced
require( './moddir/str2int.js', force=true );

str = '919';
num = str2int( str );

printv( num );

