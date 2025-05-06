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
        self.index_file = self.config.paths.get('indexfile','index.html') or 'index.html'
        print(f"{type(self)}: index_file is {self.index_file}")
        if 'documents' in self.config.paths:
            if ':' in self.config.paths.documents:
                rpath, dpath = self.config.paths.documents.split(':',1)
            else:
                rpath, dpath = 'docs', self.config.paths.documents
        else:
            raise AttributeError('File service is not configured in the configuraiton file.')
        self._plugin_id = rpath
        self.docpath = dpath

    def error_html(self,code,message):
        return f"""<html><head><title>{message}</title></head><body><h1>{code} - {message}</h1></body></html>"""
    
    async def request_handler(self, **args):
        filename = args.get('subpath',self.index_file) or self.index_file
        if not filename:
            return 400,web.Response(status=400, text=self.error_html(400,'Bad Request'), content_type='text/html')
        filename = os.path.join(self.docpath,filename)
        if not os.path.exists(filename):
            return 404,web.Response(status=404, text=self.error_html(404,"Resource Not Found"), content_type='text/html')
        if os.path.isdir(filename): # If we get a directory, append the indexfile name
            filename = os.path.join(filename,self.index_file) 
        with open(filename) as f:
            content=f.read()
        mime = mimetypes.guess_type(filename)[0]
        response = web.Response(text=content, content_type=mime)
        return 200, response