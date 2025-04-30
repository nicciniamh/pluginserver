# Plugin Server

This server implements an API server using rest-like API routes. The server is implemented in Python using aiohttp. 

This relatively simplistic RESTapi servers use routes to determine the request handler when a request is made. A route is simply the 'tail' of the web address being requested. Think of a web address like `https://server.domain.tld/tail`. The tail portion is the route. 

Requests are made up of `proto://address:port/route?parameters`. Proto would typically be http or https. Address is the ip address or hostname of the server and port is the numeric port the server listens on.

The server has various configuraiton options, which you should be familiar with. These options and formats are described in the [Configuration](Config.md) document.

## Plugins

Plugins are how this server serves data for specific routes. In my pacakaged example, I provide one plugin that responds to a /systeminfo route. When requested this route will present back a set of system data for things like cpu, disk, packages, network interfaces, uname data. For more information, please see [Plugins](Plugins.md) where this is discussed in greater detail.

## Security

Security is managed two different ways. The first is to set up SSL. To be as secure as possible a key/certificate pair signed by a known Certificate Authority, such as [Let's Encrypt](letsencrypt.org), please see [Config](Config.md) for details on setting the key and certificate values and enabling SSL. 

Self-signed certificates are not recommended and can be problematiing with other tools that make requests to the server.

Once SSL is enabled, the use of an API key is an additional layer. By passing `apikey=<pre-shared key>` within a *POST* request, if auth is enabled this key will be used to authenticate the request. Since this key is passed in *POST* data, it will not show in the URL or the server logs unless explicitly logged, which, generally, is not done. 

