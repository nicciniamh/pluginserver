# Plugins

Plugins provide the functional aspects of the plugin server. These classes provide the code to handle routers.  These routes must return immediatelt, however, async tasks can be started to handle background operations and the plugin can be queried later for results. The plugin should return JSON web responses, serialized JSON data, dicts, lists, or strings. These types, or their attributes, must be serializable to JSON. 

Plugins should be based on `plugincore.BasePlugin`. This base class handles initialization and basic task handling so the plugin doesn't have to manage that aspect of its operation. 

The BasePlugin class should be subclassed for plugins as it sets up global variables and provides utility methods. 

<pre><code>
class BasePlugin:
	  def __init__(self, **kwargs):
        self._auth_type = None
        self._apikey = None
        self.config = kwargs.get('config')
        self._plugin_id = kwargs.get('route_path',self.__class__.__name__.lower())
        self.auth_type = kwargs.get('auth')
        if self._auth_type:
            if self._auth_type.lower() == 'global':
                if 'auth' in self.config and 'apikey' in self.config.auth:
                    self._apikey = self.config.auth.apikey
            elif self.auth_type.lower() == 'plugin':
                self._apikey = kwargs.get('apikey')
            if not self._apikey:
                self._auth_type = None
        self.args = dict(kwargs)

    def _check_auth(self,data):
        if self._auth_type:
            return self._apikey == data.get('apikey')
        return True

    def _get_plugin_id(self):
        return self._plugin_id
    
    async def handle_request(self, **data):
        if self.auth_type:
            if not self._check_auth(data):
                return web.json_response({'error': 'unauthorized'}, status=403)

</code></pre>