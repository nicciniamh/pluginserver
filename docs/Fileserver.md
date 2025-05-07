# File Serving

To serve files with pluginserver the fileserve.py plugin must be used. This plugin accepts requests for files, and serves their content to the requesting client. 

## Files and Content
When a file is requested, the mime type of the file is determined using the Python mimetypes pacage so the correct content type headers before sending the content to the client. In the event the mime type cannot be determined the default of `'application/octet-stream` is used.

##  Path Resuolution
The fileserve plugin is configured for a base path, or, document root using configuration paramaters, discussed below in the [Plugin Configuration](#plugin-configuraiton) below. 

When a path is requested, it is first checked to see if it is a directory or file. If it is a file and the file is readable, its content is sent to the client. 

If the file is a directory, [configured](#plugin-configuraiton) index file is appended to the directory and service is attempted. When exceptions occur trying to serve the file appropriate errors are returned  to the client as both status codes and error text. 

## Error Handling
When Python exceptions are encountered, they are translated to HTTP status codes and error messages.

## Plugin Configuraiton

The file server plugin, fileserve.py, uses some config values to set itself up. WHen availabe and configured the file server plugin serves files out of a configured directory. 

To configure this plugin, the [configuration](Config.md) can be modified as below. In order for this configurtion work the fileserve.py plugin must me present in the `config.paths.plugins path`. 

```ini
[paths]
...
documents=html:${ENV:HOME}}/apidocs
indexfile=app.html
```

### Documents Path
The documents path may have two parts, but, one is required. The parts are separated by a colon (:). The path component before the colon is used to 'name' the request path. If this part is not defined, the basename of the path supplied is used as the request path. These variables 
are evaluated as below:

| Path                                    | Request Path | Documents Directory   |
|-----------------------------------------|--------------|-----------------------|
| `documents=html:${ENV:HOME}}/apidocs`   | html         | /home/user/apidocs    |
| `documents=/usr/share/apidocs`          | apidocs      | /usr/share/apidocs    |
| `documents=apidocs`                     | apidocs      | `<cwd>`/apidocs       |


### Index File
The optional `indexfile=app.html` key sets the default name of the file to be served when a document is not specified. If this is not set, index.html is used. 

When a document is requested, but, the path is a directory, the indexfie will be appended to that directory and service is attempted. 

When file service is requested but the access to the file is denied, i.e., it doesn't exist, access is denied by the OS or some other exception is encountered, appropriate HTTP status is sent along with an error message. 

When file service is complete without errors, a status of 200 and the contents of the file are sent to the client. 