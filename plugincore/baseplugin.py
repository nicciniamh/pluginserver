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
        auth = kwargs.get('auth_type').lower()
        if auth:
            if auth == 'global':
                if 'auth' in self.config and 'apikey' in self.config.auth:
                    self._apikey = self.config.auth.apikey
                else:
                    raise ValueError('Auth is global but no apikey in auth')
                self._auth_type = 'global'
            elif auth == 'plugin':
                self._apikey = kwargs.get('apikey')
                if not self._apikey:
                    raise ValueError('Auth is plugin but no plugin apikey')
                self._auth_type = 'plugin'
        self.args = dict(kwargs)

    def _check_auth(self,data):
        #print(f"_check_auth: {self._auth_type} apikey {self._apikey}, args {data}")
        if self._auth_type:
            user_key = data.get('apikey')
            #print(f"Checking {user_key}")
            if not user_key:
                #print("Returning false")
                return False
            keymatch = self._apikey == user_key
            #print(f"Returning keymatch {keymatch}")
            return keymatch
        #print("returning default true")
        return True

    def _get_plugin_id(self):
        return self._plugin_id
    
    async def handle_request(self, **data):
        auth_check = self._check_auth(data)
        if auth_check:
            code, response = self.request_handler(**data)
        else:
            code, response = 403, {'error': 'unauthorized'}
        if not isinstance(response,web.Response):
            response_obj = web.json_response(response,status=code)
        return response_obj   
