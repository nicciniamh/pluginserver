# Plugin Server

```{toctree}
:maxdepth: 2
:caption: Contents

Usage.md
Config.md
Auth.md
CORS.md
SSL.md
Plugins.md
Install.md
```

Plugin Server is a Python script and library to manage a REST-like API server utilizing a plugin system to handle requests to API routes. It is built upon Python async and aiohttp. These API routes get served as an endpoint, with `proto://server.domain.tld:port/route`.

# Getting Plugin Server
Plugin server is at [https://github.com/nicciniamh/pluginserver](https://github.com/nicciniamh/pluginserver)


To install, please follow instructions in the [install](Install.md) section.

## Usage
Please see the [Usage](Usage.md) section for an overview and usage of the server.

<small>This code has been tested under Debian 12 Bookworm and Pi OS Bookworm. Other than a unix-like system, there is no other system dependent code.</small>
