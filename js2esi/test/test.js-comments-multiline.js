/**
 * unit testing multi-line js comments
 * TODO: this is legacy and should be removed
 */

// no output line

//------------------------------------------------------------------------------
//### this is a simple ESI comment
// should be output as:
//   <esi:comment text="this is a simple ESI comment"/>

//------------------------------------------------------------------------------
//### this should prolly be
//### a multiline comment
// should be output as:
//   <esi:comment text="this should prolly be
//   a multiline comment"/>

