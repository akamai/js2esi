/**
 * test the include() and eval() statements.
 */

incpath1 = REQUEST_PATH;
incpath2 = 'http://example.com/path/to/component.html';
evalpath = 'http://example.com/path/to/file.esi';

eval(src=evalpath + '?someparam=foo', dca='akamaizer->esi');

try
{
  include(src       = 'http://redirect.com/' + incpath1,
          onError   = 'continue',
          ttl       = '4h',
          noStore   = 'on',
          setHeader = 'Cookie: x=y',
          method    = 'GET',
          dca       = 'none',
          );

  include(src       = 'http://redirect.com/' + incpath1,
          setHeader = ['Cookie: x=y', 'Cookie: a=b'],
          );
}
catch(e)
{
  include(src=incpath2, maxWait=100);
}

