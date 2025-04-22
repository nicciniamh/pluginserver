# Examples
In this directory you will find three plugins, under, plugins/
* cpuinfo: cpuinfo returns data from psutil about the cpu. It has plugin auth and its own API key. see [pserv.ini](#pserv.ini). 
* diskinfo: diskinfo returns information about the filesystems. type may be passed to limit the types show, and it uses global auth. 
* ifinfo: ifino is configured to set it's route name to network and uses no auth.

# pserv.ini

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
ifinfo=route_path=network               # Change route_path to network
cpuinfo=auth=plugin&apikey=foobar       # Use plugin auth and an apikey of foobar
diskinfo=auth=global                    # Use global auth (see [auth] below)

[auth]
apikey=deadbeef
```