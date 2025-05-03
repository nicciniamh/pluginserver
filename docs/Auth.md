# Authentication
The server utilizes pre-shared keys or tokens for authenticating server requests. 

## Configuring Authentication
In the server [confiuration](Config.md) there are a couple of way to set up authentication. 

### Global Authentication
In the [confiuration](Config.md) we set up a section and key,value pair, e.g., 

```ini
[auth]
apikey=<your pre-shared key here>
```

This sets up the global API key to be used

### Plugin Authentication
Plugin authentication is set up in the [confiuration](Config.md) file a little differently: 

```ini
[plugin_parms]
myplugin=auth_type=plugin&apikey=<your api key here>[&other paramaters]
```

## Authentication Methods for Clients
There are four ways of passing the pre-shared apikey to the server plugin handlers: 

1. Get data, e.g., `curl https://server.tld:port/plugin?apikey=xxx` - This is not secure.
2. Post data, e.g., `curl -X POST https://sever.tld:port/plugin -H "Content-Type: application/json" -d '{"apikey": "xxx"}'` - this is sent in the body of the request and not in the query string. This is secure.
3. Authorization header using a bearer key, e.g., ` curl -H "Authorization: Bearer xxx" https://server.tld:port/plugin` - this is secure too. 

4. X-Custom-Auth header using a bearer key, e.g., ` curl -H "X-Custom-Auth: xxx" https://server.tld:port/plugin` - this is secure too. 

