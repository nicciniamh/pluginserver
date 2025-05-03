
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

Security is managed a few different ways. The first is to set up SSL. Please see the section on [SSL](SSL.md) for details on configuring SSL. 

# Authentication
There are a few ways to authenticate the server operations. Please see [Authentication](Auth.md) for details. 

## Principle of Operation

### Startup
On startup the server reads the [configuration](Config.md) file and looks for the optional SSL and [CORS](CORS.md) [settings](Config.md). If these settings are enabled and configured properly, they are enabled. 

The [paths] section of the [configuration](Config.md) is checked for the `plugins` key and loads any Python files there as plugins. 

### Operation
Once the server is configured it listens to the port on the bindto address in the [configuration](Config.md) file. Each plugin is served by a route. Making a request to http[s]://host.domain.tld:port/<plugin> will return a JSON object by the server. 

The server will run until terminated by ^C, `SIGTERM` or `SIGKILL`. 
