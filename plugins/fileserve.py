import os
import mimetypes
from plugincore.baseplugin import BasePlugin
from aiohttp import web

def mime_for_buffer(buffer):
    mime = magic.Magic(mime=True)
    return  mime.from_buffer(buffer)

class ServeFiles(BasePlugin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        if 'documents' in self.config.paths:
            if ':' in self.config.paths.documents:
                rpath, dpath = self.config.paths.documents.split(':',1)
            else:
                rpath, dpath = 'docs', self.config.paths.documents
        self._plugin_id = rpath
        self.docpath = dpath
    
    async def request_handler(self, **args):
        filename = args.get('subpath') or 'index.htm'
        filename = os.path.join(self.docpath,filename)
        if not os.path.exists(filename):
            print(f" -- {filename} -- NOT FOUND")
            return 404,web.Response(status=404, text="<html><body><h1>404 - File Not Found</h1></body></html>", content_type='text/html')
        with open(filename) as f:
            content=f.read()
        mime = mimetypes.guess_type(filename)[0]
        print(f" -- {filename} - {mime}")
        response = web.Response(text=content, content_type=mime)
        return 200, response