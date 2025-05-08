# File Serving

To serve files with pluginserver the fileserve.py plugin must be used. This plugin accepts requests for files, and serves their content to the requesting client. 

## Files and Content
When a file is requested, the mime type of the file is determined using the Python mimetypes pacage so the correct content type headers before sending the content to the client. In the event the mime type cannot be determined the default of `'application/octet-stream'` is used.

### Markdown
Markdown ia an incredibly simple and useful way to express data. This plugin automatically converts markdown to html. The first top-level heading in the markdown file is used for the page title. This is inserted into the html template before serving the file. 

#### Markdown Styling
Markdown styling is done by default with markdown.css and highlight.css (the latter for syntax hightlighting). The highlighting CSS I used in testing was generated with pygments using `pygmentize -S default -f html > highlight.css`. 

#### Magic Variables
The file server plugin parses output (html or markdown) for 'magic' variables. These are:

| Variable   | Usage
|------------|----------------------------------------------------------------------------------|
| `@TITLE=Document Title@`    | Set the markdown document title
| `@INCLUDE=[<path>/]file@`   | Include the contents of file
| `@TIME=+format@`            | Include the time of day with optionl format
| `@FILETIME=filepath+format@`| Include the modification time of filepath with optional +format

For include, absolute paths may be used, and, are converted for user path with tilde expansion. Relative paths are made relative to the directory the markdown is served from. Included data is not parsed, it is included verbatim. 

For formatting dates the format should be a plus sign (+) followd by one or more of the following:

| Code | Usage
|------|-------------------------------------------------------
| %Y   | Year with century as a decimal number.
| %m   | Month as a decimal number [01,12].
| %d   | Day of the month as a decimal number [01,31].
| %H   | Hour (24-hour clock) as a decimal number [00,23].
| %M   | Minute as a decimal number [00,59].
| %S   | Second as a decimal number [00,61].
| %z   | Time zone offset from UTC.
| %a   | Locale's abbreviated weekday name.
| %A   | Locale's full weekday name.
| %b   | Locale's abbreviated month name.
| %B   | Locale's full month name.
| %c   | Locale's appropriate date and time representation.
| %I   | Hour (12-hour clock) as a decimal number [01,12].
| %p   | Locale's equivalent of either AM or PM.

A magic variable of `@TIME+%A %B $d, %Y@` would yield a string like "Monday May 5, 2025"

#### Markdown Configuration
To set the names for the css used, the following config parameters are used. These files should be path relative to the request path, so, for example, `[proto]://server.domain.tld:port/docs/markdown.css` would need to be located in the documents path specified in the [paths](#plugin-configuraiton) key.

```
[markdown]
markdown_css=markdown.css
highlight_css=highlight.css
```

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