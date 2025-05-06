# Plugins

Plugins provide the functional aspects of the plugin server. Each plugin sets up an endpoint, which is handled by the servers route handlers. 

Plugins are implemented as Python classes and are based on `plugincore.baseplugin.BasePlugin`.

These classes provide the code to handle endpoints. These endpoints must return immediately, however, async tasks can be started to handle background operations and the plugin can be queried later for results. In the file systemenfo.py, this method is calculate the network speeds (tx/rx) so that can be reaturned easilt. Please see the [Complex Example Plugin](#complex-example-plugin), below, to see how this can be done.

The plugin should return JSON web responses, serialized JSON data, dicts, lists, or strings. These types, or their attributes, must be serializable to JSON. My preference is for endpoints to return dictionaries as the structured data is more flexible. The choice, however, is yours.

## Plugin Naming
By default the name of the plugin's endpoint is the name of the class derived from BasePlugin, lowercased. The derived class can override this in its `__init__` method by setting `self._plugin_id` after `calling super()__init__` or by setting the name in `[plugin_parms]` using `route_path`.

## BasePlugin

The base class, `plugincore.baseplugin.BasePlugin`, handles initialization, authorization, and interaction with the server app object. On initilization the class sets up a plugin id that can be quried. The [configuraiton](Config.md) file has a section for pluginparms which is based on the basename of the plugin source, wothout the .py where parameters can be passed to the plugin's init method in kwargs. A subclass of BasePlugin can use its own init method to load up instance variables based on the plugin_parms.

Each BasePlugin derived class has a property of `self.config`. This is a dict-like object with the server's [configuraiton](Config.md).

### Request Handling with BasePlugin

When a request for a endpoint is made, the BasePlugin `handle_request` method is called, it is given the request variables are passed to handle_request in the **args parameter. The BasePlugin method `_check_auth` is called, and, if auth is enabled, checks the apikey argument against the configured apikey. Once these checks are made, the subclass's request_handler method is called.

BasePlugin.handle_request, and, in turn, the plugin's request_handler methods are passed a dict-like object, called data. This object contains all get and post variables as keys and values in data. Additionally the request headers are passed in `data['request_headers']`. This allows for a great deal  of flexibility with passing data to the plugin and controlling its output.

The request_handler method should return a tuple with a code and a str, list or dict containing the results of this request. It is vital that this data is JSON serializable. The code if successful should be 200, otherwise should be reflective of the type of error that ocurred. 

Once the request is completed it is handed back to the server's top level route handler which checks to see if [CORS](CORS.md) is enabled, and, if so checks the ACL and updates the response headers to send the proper [CORS](CORS.md) headers. This completes the endpoint service.

### Plugin Termination
In the case of simple plugins, termination is simply unloading the plugin. The BasePlugin class has a terminate_plugin that, by default, does nothing. 

For complex plugins that might allocate resoources, create tasks or other items that need to be cleaned up the plugin may overload this method to perform that cleanup. 

## The File Server Plugin (fileserve.py)
The file server plugin, fileserve.py, uses aomw config values to set itself up. WHen availabe and configured the file server plugin serves files out of a configured directory. 

To configure this plugin, the [configuration](Config.md) can be modified as below. In order for this configurtion work the fileserve.py plugin must me present in the `config.paths.plugins path`. 

```ini
[paths]
...
documents=html:${ENV:HOME}}/apidocs
indexfile=app.html
```

`documents=html:/path/to/html` the two parts are the request path, i.e., what the client requests, and the physical path where those files are. If the request path is not specified, i.e., `documents=/path/to/html` the request path will be /doc.

By default, when the request path is not set is to use /docs/. 

this key, `indexfile=app.html` sets the default name of the file to be served when a document is not specified. If this is not set, no default will be used and will generate an error if a default path is expected


```python
import os
import mimetypes
from plugincore.baseplugin import BasePlugin
from aiohttp import web

class ServeFiles(BasePlugin):
    """
    This plugin serves files. See the config document for setting up serving of files, 
    this plugin must be present for file serving to work.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.index_file = self.config.paths.get('indexfile','index.html') or 'index.html'
        print(f"{type(self)}: index_file is {self.index_file}")
        if 'documents' in self.config.paths:
            if ':' in self.config.paths.documents:
                rpath, dpath = self.config.paths.documents.split(':',1)
            else:
                rpath, dpath = 'docs', self.config.paths.documents
        else:
            raise AttributeError('File service is not configured in the configuraiton file.')
        self._plugin_id = rpath
        self.docpath = dpath

    def error_html(self,code,message):
        return f"""<html><head><title>{message}</title></head><body><h1>{code} - {message}</h1></body></html>"""
    
    async def request_handler(self, **args):
        filename = args.get('subpath',self.index_file) or self.index_file
        if not filename:
            return 400,web.Response(status=400, text=self.error_html(400,'Bad Request'), content_type='text/html')
        filename = os.path.join(self.docpath,filename)
        if not os.path.exists(filename):
            return 404,web.Response(status=404, text=self.error_html(404,"Resource Not Found"), content_type='text/html')
        if os.path.isdir(filename): # If we get a directory, append the indexfile name
            filename = os.path.join(filename,self.index_file) 
        with open(filename) as f:
            content=f.read()
        mime = mimetypes.guess_type(filename)[0]
        response = web.Response(text=content, content_type=mime)
        return 200, response
```

## Plugin Examples
These are a few examples of plugins. 

### Simple Example Plugin

This is a 'bare-bones' plugin that will run as example.py, and its endpoint will be `proto:host.domain.tld:port/example`. This shows the basic code the plugin must include to function as a plugin.

```python
from plugincore.baseplugin import BasePlugin

class Example(BasePlugin):

    def request_hanlder(**args:dict) ->tuple:
        return (200, {'example': 'Hi from Example.py'})

```

As you can see, this is very simple. If the plugin is configured for authentication the base class takes care of that and the aiohttp app class takes care of the transport. There's no need to worry about handling the transport between client and server. 

### Complex Example Plugin
This plugin defines two classes, the first is the `NetCounter`  class which wraps itself around and asyncio task to read the `psutil.net_io_counters` data. It keeps track of bytes sent and received and calulates the active data rate for a network interface. 

The second class is our `BasePlugin` derived class, `Netinfo`. In its __init__ (constructor) method a list of NetCounter objects are created and each task is started. 

When the a request is made to the to this endpoint a list of interfaces, their addresses and their io counters are returned in a JSON object. 

```python
import os
import psutil
import socket
import asyncio
import time
from plugincore.baseplugin import BasePlugin

class NetCounter:
	"""
	This class wraps an asyncio task to collect data for the amount
	of data received/transmitted over the course of the interval and converts
	to bytes per second
	"""
	def __init__(self,**kwargs):
		self.running = False
		self.data_ready = False
		self.iface = kwargs.get('iface')
		self.interval = kwargs.get('interval',2.5)
		self.tx_bps = 0
		self.rx_bps = 0

		if not self.iface:
			raise ValueError('No value for iface')
		ifdata = psutil.net_io_counters(True)
		if not self.iface in ifdata:
			raise ValueError(f"{self.iface} has no stats available")
		self.bytes_in = int(ifdata[self.iface].bytes_recv)
		self.bytes_out = int(ifdata[self.iface].bytes_sent)

	async def runner(self):
		self.running = True
		last_time = None
		while self.running:
			if last_time:
				ifdata = psutil.net_io_counters(True)[self.iface]
				indiff = ifdata.bytes_recv - self.bytes_in
				outdiff = ifdata.bytes_sent - self.bytes_out
				self.bytes_in = ifdata.bytes_recv
				self.bytes_out = ifdata.bytes_sent
				secs = time.time() - last_time
				self.tx_bps = int(outdiff/secs)
				self.rx_bps = int(indiff/secs)
				self.data_ready = True
			last_time = time.time()
			await asyncio.sleep(self.interval)
		print(f"runner for {self.iface} completed.")

	async def start(self):
		self._task = asyncio.create_task(self.runner())
		return self

	def get_speeds(self) -> tuple:
		def format(n):
			if n > 1024**3:
				factor, typ = 1024**3, 'gb'
			if n > 1024**2:
				factor, typ = 1024**2, 'mb'
			elif n > 1024:
				factor, typ = 1024, 'kb'
			else:
				factor, typ = 1,'b'
			return f"{round(n/factor,2)}{typ}ps"
		return (format(self.tx_bps),format(self.rx_bps))

class Netinfo(BasePlugin):
	def __init__(self,**kwargs):
		self.kicked = False
		self.counters = {}
		super().__init__(**kwargs)
		for iface in psutil.net_io_counters(True).keys():
			self.counters[iface] = NetCounter(iface=iface)

	async def kicker(self):
		for iface in self.counters.keys():
			await self.counters[iface].start()

	async def if_info(self,**data:dict) ->dict:
		if_info = []
		for iface, ifdata in psutil.net_if_addrs().items():
			for i in ifdata:
				if i.family == socket.AddressFamily.AF_INET:
					mask = sum(bin(int(octet)).count('1') for octet in i.netmask.split('.'))
					if iface in self.counters and self.counters[iface].data_ready:
						tx, rx = self.counters[iface].get_speeds()
					else:
						tx,rx = 'n/a','n/a'
					if_info.append({
						'iface': iface,
						'address': f"{i.address}/{mask}",
						"tx": tx,
						"rx": rx
					})
		return if_info

	def terminate_plugin(self):
		for id, counter in self.counters.items():
			counter.running = False


	async def request_handler(self,**data:dict) -> tuple:
		if not self.kicked:
			await self.kicker()
			self.kicked = True
		response_data = await self.if_info(**data)
		return (200, response_data)
```

