/**
 * test the "try { ... } catch { ... }" statement sequence.
 */

path = REQUEST_PATH;

try
{
  if ( path === '/path/to/some/resource' ) {
    try {
      // nested try-clause
      inInnerTry = 'true';
    }
    catch(e) {
      try
      {
        execute_and_fail_silently();
        inSilentTry = 'true';
      }
      inInnerExcept = 'true';
    }
  }
  inOuterTry = 'true';
}
catch(e) {
  inOuterExcept = 'true';
}

