# Authentication

## Configuring Authentication
The server utilizes pre-shared keys or tokens for authenticating server requests. There are four methods of authentication, described below. The different authentication schemes are present to allow for the greatest flexibility for the develper.

When [global authentication](#global-authentication) is enabled, the [Plugin Utilities](Usage.md#plugin-utilities) are checked for authorization. 

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

| Method                | Secure    | Example |
|-----------------------|-----------|---------|
| GET data              |  *no*     | `curl https://server.tld:port/plugin?apikey=xxx`
| POST data             |  *yes*    | `curl -X POST https://sever.tld:port/plugin -H "Content-Type: application/json" -d '{"apikey": "xxx"}'`
| Authentication Header |  *yes*    | ` curl -H "Authorization: Bearer xxx" https://server.tld:port/plugin`
| X-Custom-Auth Header  |   *yes*   | `curl -H "X-Custom-Auth: xxx" https://server.tld:port/plugin`

Using GET data is fine for testing but this is not secure. The apikey can be exposed in logs or anywhere the URL being requested is logged. Using either header authentication scheme is more secure however, Authentication header is most preferred. 

