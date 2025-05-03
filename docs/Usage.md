
# Using the Plugin Server

This server implements an API server using rest-like API routes. The server is implemented in Python using aiohttp. 

This relatively simplistic RESTapi servers use routes to determine the request handler when a request is made. A route is simply the 'tail' of the web address being requested. Think of a web address like `https://server.domain.tld/tail`. The tail portion is the route. 

Requests are made up of `proto://address:port/route?parameters`. Proto would typically be http or https. Address is the ip address or hostname of the server and port is the numeric port the server listens on.

The server has various configuraiton options, which you should be familiar with. These options and formats are described in the [Configuration](Config.md) document.

## Features

### Plugins

Plugins are how this server serves data for specific routes. In my pacakaged example, I provide one plugin that responds to a /systeminfo route. When requested this route will present back a set of system data for things like cpu, disk, packages, network interfaces, uname data. For more information, please see [Plugins](Plugins.md) where this is discussed in greater detail.

#### Plugin Utilities
The server sets up a few API routes to allow for managing plugins. The routes are: 

| Route             | Usage
|-------------------|-------------------------------------------
| /plugins          | Retrieves a list of active plugins
| /reload/<plugin>  | Reloadss a plgin
| /reload/all       | Reloads all plugins



### Security

Security is managed a few different ways. The first is to set up SSL. To be as secure as possible a key/certificate pair signed by a known Certificate Authority, such as [Let's Encrypt](https://letsencrypt.org), please see [Config](Config.md) for details on setting the key and certificate values and enabling SSL. 

Self-signed certificates are not recommended and can be problematiing with other tools that make requests to the server.

Once SSL is enabled, the use of an API key is an additional layer. By passing `apikey=<pre-shared key>` within a *POST* request, if auth is enabled this key will be used to authenticate the request. Since this key is passed in *POST* data, it will not show in the URL or the server logs unless explicitly logged, which, generally, is not done.

If [CORS](CORS.md) is enabled, an additional layer of authentication, in the form of an ACL is used. This ensures that requests only come from hosts that match that ACL.

#### Authentication
There are four ways of passing the pre-shared apikey to the server plugin handlers: 

1. Get data, e.g., `curl https://server.tld:port/plugin?apikey=xxx` - This is not secure.
2. Post data, e.g., `curl -X POST https://sever.tld:port/plugin -H "Content-Type: application/json" -d '{"apikey": "xxx"}'` - this is sent in the body of the request and not in the query string. This is secure.
3. Authorization header using a bearer key, e.g., ` curl -H "Authorization: Bearer xxx" https://server.tld:port/plugin` - this is secure too. 

4. X-Custom-Auth header using a bearer key, e.g., ` curl -H "X-Custom-Auth: xxx" https://server.tld:port/plugin` - this is secure too. 

## Principle of Operation

### Startup
On startup the server reads the [configuration](Config.md) file and looks for the optional SSL and [CORS](CORS.md) [settings](Config.md). If these settings are enabled and configured properly, they are enabled. 

The [paths] section of the [configuration](Config.md) is checked for the `plugins` key and loads any Python files there as plugins. 

### Operation
Once the server is configured it listens to the port on the bindto address in the [configuration](Config.md) file. Each plugin is served by a route. Making a request to http[s]://host.domain.tld:port/<plugin> will return a JSON object by the server. 

The server will run until terminated by ^C, `SIGTERM` or `SIGKILL`. 
