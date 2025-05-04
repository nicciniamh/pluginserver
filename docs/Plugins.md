# Plugins

Plugins provide the functional aspects of the plugin server. Each plugin sets up an endpoint, which is handled by the servers router handlers. 

Plugins are implemented as Python classes and are based on `plugincore.baseplugin.BasePlugin`.

These classes provide the code to handle endpoints. These endpoints must return immediately, however, async tasks can be started to handle background operations and the plugin can be queried later for results. In the file systemenfo.py, this method is calculate the network speeds (tx/rx) so that can be reaturned easilt. Please see the [Complex Example Plugin](#complex-example-plugin), below, to see how this can be done.

The plugin should return JSON web responses, serialized JSON data, dicts, lists, or strings. These types, or their attributes, must be serializable to JSON. My preference is for endpoints to return dictionaries as the structured data is more flexible. The choice, however, is yours. 

## BasePlugin

The base class, `plugincore.baseplugin.BasePlugin`, handles initialization, authorization, and interaction with the server app object. On initilization the class sets up a plugin id that can be quried. The [configuraiton](Config.md) file has a section for pluginparms which is based on the basename of the plugin source, wothout the .py where parameters can be passed to the plugin's init method in kwargs. A subclass of BasePlugin can use its own init method to load up instance variables based on the plugin_parms.

Each BasePlugin derived class has a property of `self.config`. This is a dict-like object with the server's [configuraiton](Config.md).

### Request Handling with BasePlugin

When a request for a endpoint is made, the BasePlugin `handle_request` method is called, it is given the request variables are passed to handle_request in the **args parameter. The BasePlugin method `_check_auth` is called, and, if auth is enabled, checks the apikey argument against the configured apikey. Once these checks are made, the subclass's request_handler method is called.

BasePlugin.handle_request, and, in turn, the plugin's request_handler methods are passed a dict-like object, called data. This object contains all get and post variables as keys and values in data. Additionally the request headers are passed in `data['request_headers']`. This allows for a great deal  of flexibility with passing data to the plugin and controlling its output.

The request_handler method should return a tuple with a code and a str, list or dict containing the results of this request. It is vital that this data is JSON serializable. The code if successful should be 200, otherwise should be reflective of the type of error that ocurred. 

Once the request is completed it is handed back to the server's top level route handler which checks to see if [CORS](CORS.md) is enabled, and, if so checks the ACL and updates the response headers to send the proper [CORS](CORS.md) headers. This completes the endpoint service.

## Simple Example Plugin

This is a 'bare-bones' plugin that will run as example.py, and its endpoint will be `proto:host.domain.tld:port/example`. This shows the basic code the plugin must include to function as a plugin.

```python
from plugincore.baseplugin import BasePlugin

class Example(BasePlugin):

    def request_hanlder(**args:dict) ->tuple:
        return (200, {'example': 'Hi from Example.py'})

```

As you can see, this is very simple. If the plugin is configured for authentication the base class takes care of that and the aiohttp app class takes care of the transport. There's no need to worry about handling the transport between client and server. 

## Complex Example Plugin
This plugin defines two classes, the first is the `NetCounter`  class which wraps itself around and asyncio task to read the `psutil.net_io_counters` data. It keeps track of bytes sent and received and calulates the active data rate for a network interface. 

The second class is our `BasePlugin` derived class, `Netinfo`. In its __init__ (constructor) method a list of NetCounter objects are created and each task is started. 

When the a request is made to the to this endpoint a list of interfaces, their addresses and their io counters are returned in a JSON object. 

```python
import os
import psutil
import socket
import asyncio
from plugincore.baseplugin import BasePlugin

class NetCounter:
    """
    This class wraps an asyncio task to collect data for the amount
    of data received/transmitted over the course of the interval and converts
    to bytes per second
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.data_ready = False
        self.iface = kwargs.get('iface')
        self.interval = kwargs.get('interval',1)
        self.tx_bps = 0
        self.rx_bps = 0

        if not self.iface:
            raise ValueError('No value for iface')
        ifdata = psutil.net_io_counters(True)
        if not self.iface in ifdata:
            raise ValueError(f"{self.iface} has no stats available")
        self.bytes_in = ifdata[self.iface].bytes_recv
        self.bytes_out = ifdata[self.iface].bytes_sent

    async def runner(self):
        last_time = None
        while True:
            if last_time:
                ifdata = psutil.net_io_counters(True)[self.iface]
                indiff = ifdata.bytes_recv - self.bytes_in
                outdiff = ifdata.bytes_sent - self.bytes_out
                secs = time.time() - last_time
                self.tx_bps = int(outdiff/secs)
                self.rx_bps = int(indiff/secs)
                self.data_ready = True
            last_time = time.time()
            await asyncio.sleep(self.interval)

    async def start(self):
        self._task = asyncio.create_task(self.runner())
        return self

    def get_speeds(self) -> tuple:
        def format(n):
            if n > 1024**3:
                factor, typ = 1024**3, 'bb'
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
        self.counters = {}
        super().__init__(**kwargs)
        for iface in psutil.net_io_counters(True).keys():
            self.counters[iface] = NetCounter(iface=iface)
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
                        tx,rx = 'N/A','N/A'
                    if_info.append({
                        'iface': iface,
                        'address': f"{i.address}/{mask}",
                        "tx": tx,
                        "rx": rx
                    })
        return if_info

    async def request_handler(self,**data:dict) -> tuple:
        response_data = await self.if_info(**data)
        return (200, response_data)
```

