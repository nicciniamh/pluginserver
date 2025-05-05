# Configuration

With the plugin server, a INI style configuration file is used to control aspects of the server and provide configuration to plugins. The configuration offers a rich set of interpolation and type conversions for config values. 

## Sections and Values

Sections are defined with [section]. Each section may have one or more key,value pairs, e.g., `certfile=ssl.cert`. 

### Value Interpolation
Values for keys may use, whole, or in part, other variables:

* Other config values in the form of `${section:key}`
* Environment variables in the form of `${ENV:ENVVAR}`
* Type conversions in the form of `type:value`

#### Type conversions

| Conversion    | Result 
| ------------- | ---------------------------------------------------------------------|
| `int:value`   | Converts *value* to integer
| `float:value `| Converts value to float
| `bool:value`  | Converts 'true' to True otherwise False
| `list:value`  | Converts items, separated by spaces until & or end of line to a list 

When creating *lists* each element of the list is converted using the same rules before being added to the list. 

## Required Sections and key,value Pairs

The plugin server has a few required sections and items needed to perform its work. 

| Section    | Items 
| ---------- | -------------------------------------------------------------------|
| `[Network]`| Network parameters: bindto and listen
| `[Paths]`  | Paths neeeded: pluginpath, optional: `documents=rpath:fspath` 

Some optional, but helpful sections

| Section          | Items 
| ---------------- | -------------------------------------------------------------------|
| `[SSL]`          | SSL parameters: enable, certfile, keyfile 
| `[plugin_parms]` | parameters for plugins. format is `<pluginname>=var1=val&var2=val`  
| `[cors]`         | Enables and configures CORS for the server. See the CORS section for pluginserver
| `[auth]`         | apikey - set the apikey to be used for authorization. See the Auth section for pluginserver


## Serving Static Files
Under `[paths]` if the optional key, documents is set, static pages may be served from the directory configured. To set this directory the parameter looks like: 

`documents=html:/path/to/html` the two parts are the request path, i.e., what the client requests, and the physical path where those files are. If the request path is not specified, i.e., `documents=/path/to/html` the request path will be /doc. 


## Example INI file

```ini
#
# Plugin server config file: 
# Like all INI files sections are noted as [section]
# any item inder a section belongs to that section. Internally this file becomes: 
# config.ssl.enabled
#       |-->.network.bindto
# or each sections has ay when the object is used as a dict and section  names are keys 
# in the dict to another dict:
#
# Values to keys may be specified as ${section:key}, e.g., ${SSL:enabled} will resolve to, below,
# [SSL]
# emanled 
# and the ${SSL:enabled} == True
#
# Special type conversions:
# config value may be converted to int, float, bool and list using type conversion notation.
# variable=int|float|bool:var are converted to int float or bools as appropriate. For bools the
# value may be any of: 'true','enabled','on','1','enable' to be true. anything else is false. 
#

## Some top level stuff, junk drawer 
[main]
domain=ducksfeet.com

[SSL]
# SSL config:
# To enable set enabled=true
# keyfile is the ssl key to use
# certfile is the certificate file to use 
enabled=bool:true
keyfile=${ENV:HOME}/etc/certs/${main:domain}-key.pem
certfile=${ENV:HOME}/etc/certs/${main:domain}.pem

[network]
# Network config parameters
# bindto is the address to bind to, can be any configured ip on the machine
# port i the port to listen on
bindto=0.0.0.0
port=int:9192

[plugin_parms]
# plugin parameters - key=value[&key=value]
# Important: 
# auth = plugin|global, if plugin, apikey must be specified and that key is used to 
#   authenticate the client
# apikey = a preshared key to use 
systeminfo=auth=global

[auth]
# auth for when a plugin sets auth=global
apikey=deadbeef

[paths]
# paths to use, so far, we define only paths for plugins. Other paths can be defined here 
# that plugins can use with self.config 
# 
plugins=${ENV:HOME}/etc/rsysinfo

[cors]
# cors
# Create allowance for cors requests behind the util in origin_url
enabled=bool:true
origin_url=list:https://pi4.ducksfeet.com https://dfrb.hopto.org
```
