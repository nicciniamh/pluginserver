# Plugin Based RESTapi Server

I have an affinity for connecting information to servers and making computers talk to each other. 

python aiohttp offsers a great way to do this, but, how to do so dynamically? Plugins!

Simplistic RESTapi servers use routes to determine the request handler when a request is made. A requests is made up of `proto://address:port/route?parameters`. Proto would typically be http or https. Address is the ip address or hostname of the server and port is the numeric port the server listens on. 

An [Example Request](#Example-Request) is show below. 

## Plugins
This module creates am aiohttp server and loads its routes from a directory of plugins. Plugins are python scripts that have some common properties:

* Derived from BasePlugin
* Has a method of handle_request which can return an aiohtto.Web.Response or a dict that is returned as a JSON resposne. 

Plugins may receive additional parameters from the [INI file](#Ini-File).

BasePlugin is defined as:

```python
class BasePlugin:
    def __init__(self, **kwargs):
        ourclass = self.__class__.__name__
        self._plugin_id = kwargs.get('route_path',ourclass.lower())
        self.args = dict(kwargs)

    def _get_plugin_id(self):
        return self._plugin_id

```

In `__init__` if the kawarg, route_path, is set (usually from the .ini config file), that value is used for the route path of the server, otherwise, the class name, lowered, is used to create the routepath. 

Example plugin: 

```python
class CpuInfo(BasePlugin):

    async def handle_request(self, **data):
        return {
            'cpu_count': psutil.cpu_count(),
            'loadavg': psutil.getloadavg(),
            'percent': psutil.cpu_percent(),
            'times': psutil.cpu_times(),
            'stats': psutil.cpu_stats()
        }
```

This creates a route for the rest server of /cpuinfo. Given this ini file: 

```ini
[network]
bindto=0.0.0.0
port=9192

[paths]
plugins=siserv/plugins


```

## Example Request

A request can be made with curl, for exmple, as: 

```bash
curl http://192.168.1.77:9192/cpuinfo
```

Which returns the data as JSON:

```json
{"cpu_count": 7, "loadavg": [0.095703125, 0.14453125, 0.11474609375], "percent": 0.4, "times": [2357.2, 0.59, 1911.99, 471369.26, 69.9, 0.0, 249.74, 0.0, 0.0, 0.0], "stats": [123506235, 69652366, 15829877, 0]}
```

## Ini File

Entries in the INI files are made with `[section]` and key,value pairs. 
Reequired items are: 

* in section `[network]` `bindto`  and `port` are needed. 
* in sections `[paths]` `plugins=` must be set to the path where the plugins are stored. 
* pkuglin parameters are specified in `[plugin_parms]` with the base name of the plugin filename, e.g., plugin.py

Section and key names must start with alpha characters (A-Z, a-z) and must not contain the names of Python keywords, Python builtins, or names of instance variables or methods within the config class, or the word self. If an invalid keyword is used AttributeError is raised with descriptive errors. 

Configuration entries can be overrideden by environment variables, but, the key must exist in the INI file. Overrides may use an environment prefix. 

```bash
export PSERV_PLUGIN_PARMS_PLUGIN.PY=restrict_info=1
```

when using this environment override, the server must be started with

```bash
pserve -f pserve.ini -e -p PSERV 
```

## Running The Server

The name of the server is pserve, it is run with any of the following parameters: 

* -f <file> use <file> for config
* -e allow environment variables to override the ini file variables as above.
* -p <prefix> prefix for environment overrides as above. 


