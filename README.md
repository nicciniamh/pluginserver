# Plugin Server

This server implements an API server using rest-like API routes. The server is implemented
in Python using aiohttp.

This relatively simplistic RESTapi servers use routes to determine the request handler when a request
is made. A route is simply the ‘tail’ of the web address being requested.
Think of a web address like `https://server.domain.tld/tail`. The tail portion is the route.

Please see the documentation at [https://pluginserver.readthedocs.io](https://pluginserver.readthedocs.io/en/latest/). 

