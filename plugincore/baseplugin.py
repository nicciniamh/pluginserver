import asyncio
from aiohttp import web
import inspect
from plugincore import logjam

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
        auth = kwargs.get('auth_type')
        args = kwargs.get('prog_args')
        if not args:
            raise ValueError(f"no args were passed")
        if auth:
            auth = auth.lower()
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
        if args.log:
            self.log = logjam.LogJam(file=args.log, name=self._plugin_id,level=args.level)
        else:
            self.log = logjam.LogJam(name=self._plugin_id,level=args.level)
        kwargs['log'] = self.log
        self.args = dict(kwargs)

    def _get_client_ip(self,request):
        # Check proxy headers first
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        # Fall back to transport address
        peername = request.transport.get_extra_info('peername')
        return peername[0] if peername else 'unknown'

    def terminate_plugin(self):
        pass

    def _check_auth(self,data):
        toktype = 'Undefined'
        def get_token(data):
            nonlocal toktype
            headers = data.get('request_headers', {})
            auth_header = headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                toktype = 'token'
                return auth_header.split(' ', 1)[1].strip()
            return None

        def get_custom_header_token(data):
            nonlocal toktype
            headers = data.get('request_headers', {})
            custom_header = headers.get('X-Custom-Auth')
            toktype = 'custom'
            if custom_header:
                return custom_header.strip()
            return None

        def get_user_token(data):
            nonlocal toktype
            token = data.get('apikey')
            if token:
                toktype='userdata'
            return token
        user_key = get_token(data) or get_custom_header_token(data) or get_user_token(data)
        #print(f"_check_auth: type: {toktype} {self._auth_type} apikey {self._apikey}, args {data}")

        if self._auth_type:
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
        request = data.get('request',{})
        auth_check = self._check_auth(data)
        data['client_ip'] = self._get_client_ip(data.get('request'))
        if auth_check:
            result = self.request_handler(**data)
            code, response = await result if inspect.isawaitable(result) else result
            #print(f"Got {code} - {response}")
        else:
            self.log.error(f"{data['client_ip']} - request for {self._plugin_id} - Not authorized")
            code, response = 403, {'error': 'unauthorized'}

        if isinstance(response, web.Response):
            pass
        elif isinstance(response, dict):
            response = web.json_response(response)
        elif isinstance(response, str):
            response = web.Response(text=response, content_type='text/html')
        else:
            response = web.json_response({'result': str(response)})
        return response
