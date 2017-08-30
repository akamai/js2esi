/**
 * test the try statement within a function definition.
 */

var path = REQUEST_PATH;

function someFunction() {
  try {
    if ( path === '/path/to/some/resource' ) {
      try
      {
        // nested try-clause
        return 'a';
      }
      catch(e) {
        try {
          // do something that does not require an catch clause
          execute_and_fail_silently();
        }
        return 'b';
      }
    }
    return 'c';
  }
  catch(e) {
    return 'd';
  }
}

