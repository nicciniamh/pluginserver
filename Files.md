## Plugin Server Files


### docs/ Documentation for the plugin server

| File             |  Description
|----------------- | ---------------------------------------------------
| Auth.md          | Authorization and security docs
| Config.md        | Configuration docs
| conf.py          | For sphinx/rtd
| CORS.md          | CORS explaination and config
| Fileserver.md    | Filesever operations
| index.md         | Base document
| Plugins.md       | Plugin docs and how to
| requirements.txt | For sphinx/rtd
| Sessman.md       | Session manager docs
| SSL.md           | SSL Docs
| Usage.md         | General usage notes

### plugincore/ Core of the plugin server

| File             |  Description
|----------------- | ---------------------------------------------------
| baseplugin.py    | Baseplugin module to standardize plugin objects
| configfile.py    | Configuration file parser
| logjam.py        | Logging code 
| pluginmanager.py | Plugin manager code

### plugins/ Standard plugins

| File             |  Description
|----------------- | ---------------------------------------------------
| fileserve.py     | File server plugin
| sessman.py       | Session manager plugin
| systeminfo.py    | systeminformation plugin

