# Plugin Server

```{toctree}
:maxdepth: 2
:caption: Contents

Usage.md
Config.md
Plugins.md
Fileserver.md
Auth.md
CORS.md
SSL.md
Sessman.md
```
# Plugin Server is a Python script and library to manage a REST-like API server utilizing a plugin system to handle requests to API routes. It is built upon Python async and aiohttp. These API routes get served as an endpoint, with `proto://server.domain.tld:port/route`.

# *Warning: This is alpha level code, some of the examples may not work. Please stand by!*

## Intended Audience
This document and code are intended for people familiar with Linux, System Administration and the Python programming language. 

## Installing Plugin Server

To install the stable version of this project, use [PyPi](https://pypi.org/project/pluginserver/) with:

```bash
pip install pluginserver
```

To install the latest commits to Plugin Server, use the following command:

```bash
pip install git+https://github.com/nicciniamh/pluginserver.git
```

Or you can clone [https://github.com/nicciniamh/pluginserver.git](https://github.com/nicciniamh/pluginserver.git) and install with pip install pluginserver

If you just want the example rsysinfo service, clone: 

```bash
git clone https://github.com/nicciniamh/pluginserver_examples.git
```

<small>This code has been tested under Debian 12 Bookworm and Pi OS Bookworm. Other than a unix-like system, there is no other system dependent code.</small>
