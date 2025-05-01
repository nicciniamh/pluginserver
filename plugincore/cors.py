from aiohttp import web
import aiohttp_cors
import aiohttp_cors
from aiohttp import web
import re
from urllib.parse import urlparse

class CORS:
    def setup(self, app, globalCfg):
        self.origins = []
        self.acl = []
        self.config = globalCfg
        self.cors_enabled = False

        # Check if CORS is enabled in the config
        if 'cors' in self.config:
            if 'enabled' in self.config.cors:
                self.cors_enabled = self.config.cors.enabled  # Assuming this is a boolean
            if self.cors_enabled:
                # If enabled, fetch the allowed origins
                if 'origin_url' in self.config.cors:
                    self.origins = self.config.cors.origin_url  # List of allowed origins
                else:
                    # If origin_url is not set, disable CORS
                    self.cors_enabled = False
            if self.cors_enabled:
                if 'acl' in self.config.cors:
                    self.acl = self.config.cors.acl
                    print(f"CORS setup, acl {self.acl}")

        
        # If CORS is enabled, set it up with aiohttp_cors
        if self.cors_enabled:
            print(f"CORS Setup - ORIGIN URLs: {self.origins}")
            cors = aiohttp_cors.setup(app)
            for route in list(app.router.routes()):
                cors.add(route, {
                    'origins': self.origins,
                    'allow_credentials': True,
                    'expose_headers': "*",
                    'allow_headers': "*",
                    'allow_methods': ["GET", "POST", "OPTIONS"]
                })

        return self

    def _add_header(self, response, request):
        """Add the CORS headers to the response."""
        request_origin = request.headers.get('Origin')
        if request_origin == 'null':
            request_origin = None
        if not request_origin:
            return response
        host_name = urlparse(request_origin).hostname

        request_ok = True
        if self.cors_enabled and request_origin:
            if request_origin in self.origins:
                response.headers['Access-Control-Allow-Origin'] = request_origin
            else:
                request_ok = False
                if self.acl:
                    for a in self.acl:
                        pattern = r'^[a-zA-Z0-9.-]*\.' + re.escape(a) + r'$|^' + re.escape(a) + r'$'
                        if re.match(pattern,urlparse(request_origin).hostname):
                            request_ok = True
                            break
                if not request_ok:
                    return web.HTTPForbidden(text="CORS origin not allowed")
            
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Vary'] = 'Origin'
        return response

    def apply_headers(self, response, request):
        """Apply CORS headers based on the response type."""
        # Skip the CORS logic if CORS is disabled
        if not self.cors_enabled:
            return response  # No CORS logic applied

        if isinstance(response, web.Response):
            response = self._add_header(response, request)
        elif isinstance(response, dict):
            response = self._add_header(web.json_response(response), request)
        elif isinstance(response, str):
            response = self._add_header(web.Response(text=response, content_type='text/html'), request)
        else:
            response = self._add_header(web.json_response({'result': str(response)}), request)

        response.headers['X-Content-Type-Options'] = 'nosniff'  # Security header
        return response
