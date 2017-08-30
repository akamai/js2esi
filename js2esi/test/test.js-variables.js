/**
 * unit testing js variables (assignment, defaulting, accessing, etc)
 */

// TODO: support range expressions, eg:
// TODO:   $varRange = [ 0 .. 7, 10..15];

let varInteger = 299;
varString = 'DOS sucked back then';
varVarExpr = varString + ', renamed to Vista doesnt help';
varArray[8] = 'ninth element';
varHash['foo'] = 'fooeth element' + varArray[8];
varHash['foo'] += '88';
varNegative = -38;
varTabString = '2-tabs:		8-spaces:        ';
varNegative -= 10;
varNegative += 10;
varString += ' (this is a fact)';
varInteger *= 10;
varInteger /= 10;
varInteger %= 10;
varHash[varName] = 'advanced use?';
varInteger++;
varInteger--;

// test defaulting
varWDef = QUERY_STRING['foo'] || 'NaDa';

