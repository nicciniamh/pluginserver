# Plugins

Plugins provide the functional aspects of the plugin server. Each plugin sets up an endpoint, which is handled by the servers router handlers. 

Plugins are implemented as Python classes and are based on `plugincore.baseplugin.BasePlugin`.

These classes provide the code to handle endpoints. These endpoints must return immediately, however, async tasks can be started to handle background operations and the plugin can be queried later for results. In the file systemenfo.py, this method is calculate the network speeds (tx/rx) so that can be reaturned easilt. Please see the [Plugin Sever Examples](https://github.com/nicciniamh/pluginserver_examples) for the systeminfo plugin. 

The plugin should return JSON web responses, serialized JSON data, dicts, lists, or strings. These types, or their attributes, must be serializable to JSON. My preference is for endpoints to return dictionaries as the structured data is more flexible. The choice, however, is yours. 

## BasePlugin

The base class, `plugincore.baseplugin.BasePlugin`, handles initialization, authorization, and interaction with the server app object. On initilization the class sets up a plugin id that can be quried. The [configuraiton](Config.md) file has a section for pluginparms which is based on the basename of the plugin source, wothout the .py where parameters can be passed to the plugin's init method in kwargs. A subclass of BasePlugin can use its own init method to load up instance variables based on the plugin_parms.

Each BasePlugin derived class has a property of `self.config`. This is a dict-like object with the server's [configuraiton](Config.md).

### Request Handling with BasePlugin

When a request for a endpoint is made, the BasePlugin `handle_request` method is called, it is given the request variables are passed to handle_request in the **args parameter. The BasePlugin method `_check_auth` is called, and, if auth is enabled, checks the apikey argument against the configured apikey. Once these checks are made, the subclass's request_handler method is called.

BasePlugin.handle_request, and, in turn, the plugin's request_handler methods are passed a dict-like object, called data. This object contains all get and post variables as keys and values in data. Additionally the request headers are passed in `data['request_headers']`. This allows for a great deal  of flexibility with passing data to the plugin and controlling its output.

The request_handler method should return a tuple with a code and a str, list or dict containing the results of this request. It is vital that this data is JSON serializable. The code if successful should be 200, otherwise should be reflective of the type of error that ocurred. 

Once the request is completed it is handed back to the server's top level route handler which checks to see if [CORS](CORS.md) is enabled, and, if so checks the ACL and updates the response headers to send the proper [CORS](CORS.md) headers. This completes the endpoint service.

## Example Plugin

This is a 'bare-bones' plugin that will run as example.py, and its endpoint will be `proto:host.domain.tld:port/example`.

```python
from plugincore.baseplugin import BasePlugin

class Example(BasePlugin):

    def request_hanlder(**args):
        return 200, {'example': 'Hi from Example.py'}

```

As you can see, this is very simple. If the plugin is configured for authentication the base class takes care of that and the aiohttp app class takes care of the transport. There's no need to worry about handling the transport between client and server. 

