/**
 * unit testing js "foreach" loops
 */

days = [1 .. 31];

for (const day of days) {
  bananas = day * 3;
  print('With three bananas per day, on day ', day, ', we have ', bananas, ' bananas.\n');
}

// foreach can be used without an explicit iteration container name, which
// defaults to "item".
for (item of days) {
  print('Day ' + item + ' - nothing to report.\n');
}

// and this is to detect that the container name is redundant.
for (item of ([1..365])) {
  if ( item == 31 )
    break;
  print('Day ' + item + ' - really, nothing to report.\n');
}

