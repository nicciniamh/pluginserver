# Plugin Based RESTapi Server

I have an affinity for connecting information to servers and making computers talk to each other. 

python aiohttp offsers a great way to do this, but, how to do so dynamically? Plugins!

Simplistic RESTapi servers use routes to determine the request handler when a request is made. A requests is made up of `proto://address:port/route?parameters`. Proto would typically be http or https. Address is the ip address or hostname of the server and port is the numeric port the server listens on. 

## INI File

Entries in the INI files are made with `[section]` and key,value pairs. Some sections are required.

Example INI File:

```ini
[SSL]
enabled=true
certfile=/home/nicci/etc/ssl/pserve.crt
keyfile=/home/nicci/etc/ssl/pserve.key

[network]
bindto=0.0.0.0
port=9192

[paths]
plugins=plugins

[plugin_parms]
ifinfo=route_path=network
cpuinfo=auth=plugin&apikey=foobar
diskinfo=auth=global

[auth]
apikey=deadbeef
```

### INI File Sections

|Section       | Required | Function                          |
|--------------|----------|-----------------------------------|
| SSL          |    X     | Sets parameeters for SSL          | 
| network      |    ✓     | Sets up network parameters        |
| paths        |    ✓     | Define paths for operations       |
| plugin_parms |    X     | Define parameters for plugins     |
| auth         |    X     | Global authorization settings     |

Sections by name:

* [auth]: apikey= pre-shared key for global authorization
 global=required to make all plugins use global auth unless plugin auth is defined.
* [networ]: bindto= the network interface address to bind to. port= the network port to use. 
* [paths]: plugins= the path where the plugins are loaded from
* [plugin_parms]: additional plugin parameters 
* [SSL]: enabled= true if SSL is enabled, certfile and keyfile for the certificate and key, both
   must be defined.

Section and key names must start with alpha characters (A-Z, a-z) and must not contain the names of Python keywords, Python builtins, or names of instance variables or methods within the config class, or the word self. If an invalid keyword is used AttributeError is raised with descriptive errors. 

Configuration entries can be overrideden by environment variables, but, the key must exist in the INI file. Overrides may use an environment prefix. 

## Running The Server

The name of the server is pserve, it is run with any of the following parameters: 

* -f <file> use <file> for config
* -e allow environment variables to override the ini file variables as above.
* -p <prefix> prefix for environment overrides as above. 

## Plugins

Plugins perform the actual server work. The pserver program sets things up but, without plugins,
does nothing terribly useful. 

### BasePlugin
BasePlugin is the class on which plugins should be based. The constructor sets up the route name, 
authorization type and apikeys is they are specified. The server calls the BasePlugin method handle_request which checks for any authorization, and if successful, hands off the work to the 
derived class (your plugin)'s `request_handler` method.

While BasePlugin sets up the plugin 'infrastructure', typically, the BasePlugin methods are not called by the derived class. Two instances variables that may be important to the derived class 
are self.config, which contains the server configuraiton data, and self.args which contain the
kwargs used when instantiating the object. This includes the key,value pairs from the 
plugin_parms config section for the particular plugin. 

### Example Plugin

This plugin returns a dict, which is later retured by the server as a JSON object, containing
some information about the CPU

```python
from plugincore.baseplugin import BasePlugin    # Plugin framework
from aiohttp import web                         # Needed for response generation
import psutil                                   # Does the heavy liftin

class CpuInfo(BasePlugin):
    def request_handler(self, **data):
        cpudata = {
            'cpu_count': psutil.cpu_count(),
            'loadavg': psutil.getloadavg(),
            'percent': psutil.cpu_percent(),
            'times': psutil.cpu_times(),
            'stats': psutil.cpu_stats()
        }
        key = data.get('key')
        if key:
            if key in cpudata:
                robj = {key: cpudata[key]}
            else:
                return web.json_response({'error': f"key, {key}, not found."}, status=400)
        else:
            robj = cpudata
        
        return web.json_response(robj, status=200)
        
```

This plugin returns a dict of CPU information. If the key is specified, the data for that key is returned or a not found error if the key doesn't exist.

Exampe usage:

Getting the full dictionary: 

```bash
curl -k https://192.168.1.77:9192/cpuinfo?apikey=myapikey
```

Returns: 

```json
{"cpu_count": 7, "loadavg": [0.01708984375, 0.05029296875, 0.03662109375], "percent": 1.2, "times": [5306.68, 0.92, 3518.19, 1032672.71, 134.64, 0.0, 465.12, 0.0, 0.0, 0.0], "stats": [227322644, 129250156, 31837048, 0]}
```

Getting just the times item: 

```bash
curl -k https://192.168.1.77:9192/cpuinfo?apikey=foobar&key=times
```

Returns

```json
{"times": [5291.78, 0.92, 3509.42, 1030631.58, 134.41, 0.0, 463.98, 0.0, 0.0, 0.0]}
```

