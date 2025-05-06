import os
import mimetypes
from plugincore.baseplugin import BasePlugin
from aiohttp import web

class ServeFiles(BasePlugin):
    """
    This plugin serves files. See the config document for setting up serving of files, 
    this plugin must be present for file serving to work.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(f"-- paths: {self.config.paths}")
        if 'documents' in self.config.paths:
            if ':' in self.config.paths.documents:
                rpath, dpath = self.config.paths.documents.split(':',1)
            else:
                rpath, dpath = 'docs', self.config.paths.documents
        else:
            raise AttributeError('File service is not configured in the configuraiton file.')
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