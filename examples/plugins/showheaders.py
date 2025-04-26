from plugincore.baseplugin import BasePlugin
from aiohttp import web

class ShowHeaders(BasePlugin):
    def request_handler(self, **data):
        response = web.json_response({'status': 'success - data written to log'})
        try:
            print(f"{data}")
        except:
            response = web.json_response({'status':'fail'})
        return response;
