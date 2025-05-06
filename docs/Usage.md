
# Using the Plugin Server

This server implements an API server using rest-like API endpoints. The server is implemented in Python using aiohttp.
The server has various configuraiton options, which you should be familiar with. These options and formats are described in the [Configuration](Config.md) document.

### Endpoints and Routes

* A route is a path the server uses to retrieve and serve data from a plugin. For example, /systeminfo would be a route.
* An endpoint is the full path for the request, e.g., `https://server.domain.tld:port/systeminfo`.

Requests made to an endpoint, invokes the server's route handler, which is typically a [plugin](Plugins.md) which returns data to the server, which, in turn, returns data to the device making the request.

## Features

### Plugins

Plugins perform the API handling for the server and create the API endpoints. When the server recives a request, the path portion of the URL is the endpoint, and, the server uses that path to route the request to the appropriate plugin. Plugins are discussed in detail in the [Plugins](Plugins.md) section.

#### Plugin Utilities
The server sets up a few API endpoints to allow for managing plugins. When [authentication](Auth.md) is configured, the global apikey is used to authenticate these utilities.

These are the Plugin Utilities:

| Route                 | Usage
|-----------------------|-----------------------------------------------
| `/plugins`            | Retrieves a list of active plugins
| `/reload/<plugin>`    | Reloadss a plgin
| `/reload/all`         | Reloads all plugins
| `todo: /load<plugin>` | todo: load a plugin while the server is running


### Security

Security is managed a few different ways. The first is to set up SSL. Please see the section on [SSL](SSL.md) for details on configuring SSL. 

### Authentication
There are a few ways to authenticate the server operations. Please see [Authentication](Auth.md) for details. 

### Static File Service
As this is a server based on plugins, the server component that serves static files is implemented as a plugin. Thus, the server be configured to serve static files. To configure this service, the [configuration](Config.md) can be modified as below. In order for this configurtion work the fileserve.py plugin must me present in the `config.paths.plugins path`. 

```ini
[paths]
...
documents=html:/home/nicci/test/docs
indexfile=app.html
```

`documents=html:/path/to/html` the two parts are the request path, i.e., what the client requests, and the physical path where those files are. If the request path is not specified, i.e., `documents=/path/to/html` the request path will be /doc.

By default, when the request path is not set is to use /docs/. 

this key, `indexfile=app.html` sets the default name of the file to be served when a document is not specified. If this is not set, no default will be used and will generate an error if a default path is expected


## Principle of Operation

### Startup
On startup the server reads the [configuration](Config.md) file and looks for the optional SSL and [CORS](CORS.md) [settings](Config.md). If these settings are enabled and configured properly, they are enabled. 

The [paths] section of the [configuration](Config.md) is checked for the `plugins` key and loads any Python files there as plugins. 

### Operation
Once the server is configured it listens to the port on the bindto address in the [configuration](Config.md) file. Each plugin is serviced by a route. The server and route become an API endpoint, which looks like `http[s]://server.domain.tld:port/<plugin>`. Making a request to this endpoint will return a JSON object by the server. 

The server will run until terminated by ^C, `SIGTERM` or `SIGKILL`. 
