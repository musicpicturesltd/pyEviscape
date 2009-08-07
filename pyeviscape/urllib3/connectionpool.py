import logging
log = logging.getLogger(__name__)

from Queue import Queue, Empty, Full
from StringIO import StringIO
from itertools import count

from urllib import urlencode
from httplib import HTTPConnection, HTTPException
from socket import error as SocketError, timeout as SocketTimeout


from filepost import encode_multipart_formdata

## Exceptions

class HTTPError(Exception):
    "Base exception used by this module."
    pass

class MaxRetryError(HTTPError):
    "Raised when the maximum number of retries is exceeded."
    pass

class TimeoutError(HTTPError):
    "Raised when a socket timeout occurs."
    pass

## Response objects

class HTTPResponse(object):
    """
    HTTP Response container.

    Similar to httplib's HTTPResponse but the data is pre-loaded.
    """
    def __init__(self, data='', headers={}, status=0, version=0, reason=None, strict=0):
        self.data = data
        self.headers = headers
        self.status = status
        self.version = version
        self.reason = reason
        self.strict = strict

    @staticmethod
    def from_httplib(r):
        """
        Given an httplib.HTTPResponse instance, return a corresponding
        urllib3.HTTPResponse object.

        NOTE: This method will perform r.read() which will have side effects
        on the original http.HTTPResponse object.
        """
        return HTTPResponse(data=r.read(),
                    headers=dict(r.getheaders()),
                    status=r.status,
                    version=r.version,
                    reason=r.reason,
                    strict=r.strict)

    # Backwards-compatibility methods for httplib.HTTPResponse
    def getheaders(self):
        return self.headers

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

## Pool objects

class HTTPConnectionPool(object):
    """
    Thread-safe connection pool for one host.

    New connections are created only when there are no free connections
    available. Up to ``maxsize`` connections are saved for future use.
    All requests made to this object must belong to the same host as defined
    in the instantiation of this object in ``host``. If you need many hosts,
    make one instance per host.
    Socket request timeout will be set to ``timeout`` for each individual query.
    """
    def __init__(self, host, port=80, timeout=None, maxsize=10):
        self.pool = Queue(maxsize)
        self.host = host
        self.port = int(port)
        self.timeout = timeout
        self.num_connections = count()
        self.num_requests = count()

    @staticmethod
    def get_host(url):
        """
        Given a url, return its host and port (None if it's not there).

        For example:
        >>> HTTPConnectionPool.get_host('http://google.com/mail/')
        google.com, None
        >>> HTTPConnectionPool.get_host('google.com:80')
        google.com, 80
        """
        # This code is actually similar to urlparse.urlsplit, but much
        # simplified for our needs.
        port = 80
        if '//' in url:
            scheme, url = url.split('//', 1)
        if '/' in url:
            url, path = url.split('/', 1)
        if ':' in url:
            url, port = url.split(':', 1)
            port = int(port)
        return url, port

    @staticmethod
    def from_url(url, timeout=None, maxsize=10):
        """
        Given a url, return an HTTPConnectionPool instance of its host.

        This is a shortcut for not having to determine the host of the url
        before creating an HTTPConnectionPool instance.
        """
        host, port = HTTPConnectionPool.get_host(url)
        return HTTPConnectionPool(host, port=port, timeout=timeout, maxsize=maxsize)

    def _get_conn(self):
        """
        Get a connection. Will return a pooled connection if one is available.
        Otherwise, a fresh connection is returned.
        """
        try:
            conn = self.pool.get(block=False)
        except Empty, e:
            log.info("Starting new HTTP connection (%d): %s" % (self.num_connections.next(), self.host))
            conn = HTTPConnection(host=self.host, port=self.port)
        return conn

    def _put_conn(self, conn):
        """
        Put a connection back into the pool.
        If the pool is already full, the connection is discarded because we
        exceeded maxsize. If connections are discarded frequently, then maxsize
        should be increased.
        """
        try:
            self.pool.put(conn, block=False)
        except Full, e:
            log.warning("HttpConnectionPool is full, discarding connection: %s" % self.host)

    def urlopen(self, method, url, body=None, headers={}, retries=3, redirect=True):
        """
        Get a connection from the pool and perform an HTTP request.

        method
            HTTP request method (such as GET, POST, PUT, etc.)

        body
            Data to send in the request body (useful for creating POST requests,
            see HTTPConnectionPool.post_url for more convenience).

        headers
            Custom headers to send (such as User-Agent, If-None-Match, etc.)

        retries
            Number of retries to allow before raising a MaxRetryError exception.

        redirect
            Automatically handle redirects (status codes 301, 302, 303, 307),
            each redirect counts as a retry.
        """
        if retries < 0:
            raise MaxRetryError("Max retries exceeded for url: %s" % url)

        conn = self._get_conn()

        # Make the request
        try:
            self.num_requests.next()
            conn.request(method, url, body=body, headers=headers)
            conn.sock.settimeout(self.timeout)
            httplib_response = conn.getresponse()

            # from_httplib will perform httplib_response.read() which will have
            # the side effect of letting us use this connection for another
            # request.
            response = HTTPResponse.from_httplib(httplib_response)

            self._put_conn(conn)
        except (SocketTimeout), e:
            raise TimeoutError("Connection timed out after %f seconds" % self.timeout)
        except (HTTPException, SocketError), e:
            log.warn("Retrying (%d attempts remain) after connection broken by '%r': %s" % (retries, e, url))
            return self.urlopen(method, url, body, headers, retries-1, redirect) # Try again

        # Handle redirection
        if redirect and response.status in [301, 302, 303, 307] and 'location' in response.headers: # Redirect, retry
            log.info("Redirecting %s -> %s" % (url, response.headers.get('location')))
            return self.urlopen(method, response.headers.get('location'), body, headers, retries-1, redirect)

        return response

    def get_url(self, url, fields={}, headers={}, retries=3, redirect=True):
        """
        Wrapper for performing GET with urlopen (see urlopen for more details).

        Supports an optional ``fields`` parameter of key/value strings. If
        provided, they will be added to the url.
        """
        if fields:
            url += '?' + urlencode(fields)
        return self.urlopen('GET', url, headers=headers, retries=retries, redirect=redirect)

    def post_url(self, url, fields={}, headers={}, retries=3, redirect=True):
        """
        Wrapper for performing POST with urlopen (see urlopen for more details).

        Supports an optional ``fields`` parameter of key/value strings AND
        key/filetuple. A filetuple is a (filename, data) tuple. For example:

        fields = {
            'foo': 'bar',
            'foofile': ('foofile.txt', 'contents of foofile'),
        }

        NOTE: If ``headers`` are supplied, the 'Content-Type' value will be
        overwritten because it depends on the dynamic random boundary string
        which is used to compose the body of the request.
        """
        body, content_type = encode_multipart_formdata(fields)
        headers.update({'Content-Type': content_type})
        return self.urlopen('POST', url, body, headers=headers, retries=retries, redirect=redirect)
