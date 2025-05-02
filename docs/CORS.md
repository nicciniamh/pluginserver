# CORS - Cross-Origin Resource Sharing (CORS)

The plugin server can be configured to send CORS origin headers based on the 
server configuration. 

## Summary of CORS

CORS is a browser security feature that restricts web pages from making requests to a different domain than the one that served the web page. This prevents malicious websites from accessing sensitive data from other sites.

### Key Concepts

* **Origin:** Defined by the protocol (e.g., `http`, `https`), domain (e.g., `example.com`), and port (e.g., `:80`, `:443`). Two URLs have the same origin only if all three components match exactly.
* **Cross-Origin Request:** A request made from a script running on one origin to a resource on a different origin.
* **Preflight Request (OPTIONS):** For certain "complex" requests (e.g., using HTTP methods other than `GET`, `HEAD`, or `POST` with certain content types), the browser sends a preliminary `OPTIONS` request to the server to check if the actual request is allowed.
* **HTTP Headers:** CORS relies on specific HTTP headers exchanged between the browser and the server.

### Common CORS-related Headers

**Request Headers (Browser -> Server):**

* `Origin`: Indicates the origin of the request.

**Response Headers (Server -> Browser):**

* `Access-Control-Allow-Origin`: Specifies the origin(s) that are allowed to access the resource (can be `*` for any origin, but this is generally not recommended for security reasons).
* `Access-Control-Allow-Methods`: Specifies the allowed HTTP methods (e.g., `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`).
* `Access-Control-Allow-Headers`: Specifies which request headers can be used when making the actual request.
* `Access-Control-Expose-Headers`: Specifies which response headers can be accessed by the client-side script.
* `Access-Control-Allow-Credentials`: Indicates whether the actual request can include user credentials like cookies or authorization headers (`true` or `false`).
* `Access-Control-Max-Age`: Specifies the duration (in seconds) for which the preflight request can be cached.

### How CORS Works (Simplified)

1.  The browser makes a cross-origin request.
2.  The server responds with CORS-related headers.
3.  The browser checks these headers.
4.  If the headers indicate that the request is allowed based on the origin, method, and headers, the browser allows the response to be processed by the client-side script. Otherwise, the browser blocks the request or the processing of the response.

### Why is CORS Important?

CORS is a crucial security mechanism that helps protect users from cross-site scripting (XSS) and other malicious attacks by preventing unauthorized access to resources.


## CORS within Plugin Server
The plugin server CORS module works in two different ways. It uses the standard CORS headers and OPTIONS requests, but, also, if there is no CORS headers, it also performs an ACL check against the requesting host. This ACL check is optional but adds another layer of security. 

### Configuration of CORS 
CORS is implemented in the plugin server with a few [connfiguration](Config.md) key,value pairs under [CORS}

| Key           | Value/Usage
|---------------|------------
| enabled       | `bool:true`
| origin_url	   | `list:https://host1.domain1.tld https://host2.domain2.tld`
| acl			   | `list:[host.]domain.tld`, etc.

The minimal requirement is for enabled to be true and origin url to be populated.