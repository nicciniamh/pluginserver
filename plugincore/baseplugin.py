from aiohttp import web

class BasePlugin:
    """
    This is the base class for plugincore plugins. 
    The constructor handles setting up the instance variables so the 
    plugin can play nicely with the plugin manager.
    """
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

        return self.request_handler(**data)
    
