# Plugins

Plugins provide the functional aspects of the plugin server. These classes provide the code to handle routers.  These routes must return immediatelt, however, async tasks can be started to handle background operations and the plugin can be queried later for results. The plugin should return JSON web responses, serialized JSON data, dicts, lists, or strings. These types, or their attributes, must be serializable to JSON. 

Plugins should be based on `plugincore.BasePlugin`. This base class handles initialization and basic task handling so the plugin doesn't have to manage that aspect of its operation. 

The BasePlugin class should be subclassed for plugins as it sets up global variables and provides utility methods.

## BasePlugin

BasePlugin has a few required and optional kwargs:

| kwarg       | Required | Usage
|-------------|----------|-----------------------------------------
| config      |    ✓     | This is the global configuration object
| route_path  |    *     | Optionally set the route path
| auth_type   |    *     | Set the plugin auth type, values are global or plugin

(*) denotes parameters passed via the config.plugin_parms.\<plugin module\> seetting in the [configuration](Config.md). 

### Request Handling with BasePlugin

When a request for a route is made, the BasePlugin `handle_request` method is called, it is given the request variables are passed to handle_request in the **args parameter. The BasePlugin method `_check_auth` is called, and, if auth is enabled, checks the apikey argument against the configured apikey. Once these checks are made, the subclass's request_handler method is called.

BasePlugin.handle_request, and, in turn, the plugin's request_handler methods are passed a dict-like object, called data. This object contains all get and post variables as keys and values in data. Additionally the request headers are passed in `data['request_headers']`. This allows for a great deal  of flexibility with passing data to the plugin and controlling its output.

The request_handler method should return a tuple with a code and a str, list or dict containing the results of this request. It is vital that this data is JSON serializable. The code if successful should be 200, otherwise should be reflective of the type of error that ocurred. 

Once the request is completed it is handed back to the server's top level route handler which checks to see if [CORS](CORS.md) is enabled, and, if so checks the ACL and updates the response headers to send the proper [CORS](CORS.md) headers.

## Example Plugin

This is a 'bare-bones' plugin that will run as example.py, and it's route will be /example.

```python
from plugincore.baseplugin import BasePlugin

class Example(BasePlugin):

    def request_hanlder(**args):
        return 200, {'example': 'Hi from Example.py'}

```

As you can see, this is very simple. If the plugin is configured for authentication the base class takes care of that and the aiohttp app class takes care of the transport. There's no need to worry about handling the transport between client and server. 

