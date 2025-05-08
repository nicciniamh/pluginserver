import os
import mimetypes
import re
from plugincore.baseplugin import BasePlugin
from aiohttp import web
try:
    import markdown
except ImportError:
    markdown = None

class ServeFiles(BasePlugin):
    """
    This plugin serves files. See the config document for setting up serving of files, 
    this plugin must be present for file serving to work.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.highlight_css = 'highlight.css'
        self.markdown_css = 'markdown.css'
        if 'markdown' in self.config:
            for k in ['highlight','markdown']:
                css = self.config.markdown.get(f"{k}_css",f"{k}.css") or f"{k}.css"
                setattr(self,f"{k}_css",css)
        else:
            self.log(f"{type(self)}: WARN: No markdown section in {self.config}")
        self.index_file = self.config.paths.get('indexfile','index.html') or 'index.html'
        self.log(f"{type(self)}: index_file is {self.index_file}")
        self.log(f"{type(self)}: markdown_css is {self.markdown_css}")
        self.log(f"{type(self)}: highlight_css is {self.highlight_css}")
        if 'documents' in self.config.paths:
            if ':' in self.config.paths.documents:
                rpath, dpath = self.config.paths.documents.split(':',1)
            else:
                rpath, dpath = os.path.basename(self.config.paths.documents), self.config.paths.documents
        else:
            raise AttributeError('File service is not configured in the configuraiton file.')
        self._plugin_id = rpath
        self.docpath = dpath

    def error_html(self,code,message):
        return f"""<html>
            <head>
                <title>{message}</title>
            </head>
            <body>
                <h1>{code} - {message}</h1>
            </body>
        </html>"""
    
    def markdown_to_html(self, md, basepath):
        title = ""
        lines = md.split('\n')
        data_out = []
        def include_file(name):
            nonlocal basepath
            nonlocal data_out
            name=os.path.expanduser(name)
            if not name.startswith('/'):
                filename = os.path.join(basepath,name)
            else:
                filename = name
            try:
                with open(filename) as f:
                    for line in f.read().strip().split('\n'):
                        data_out.append(line)
            except Exception as e:
                print(f"Cannot include {filename}: {e}")
                pass

        def set_title(new_title):
            nonlocal title
            title = new_title

        processors = {'@INCLUDE': include_file,'@TITLE':set_title}
        for line in lines:
            if not title:
                match = re.match(r'^\s*#\s+(.*)$',line)
                if match:
                    set_title(match.group(1).strip())
            if line.strip().startswith('@') and '=' in line:
                cmd,value = line.strip().split('=',1)
                if cmd in processors:
                    processors[cmd](value)
            else:
                data_out.append(line)
        md = '\n'.join(data_out)
        mdhtml = markdown.markdown(md, extensions=['fenced_code', 'codehilite'])  # Enable the fenced_code extension
        return f"""<!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
                <link rel="stylesheet" href="{self.markdown_css}">
                <link rel="stylesheet" href="{self.highlight_css}">
            </head>
            <body>
                {mdhtml}
            </body>
            </html>"""

    async def request_handler(self, **args):
        code = 200
        request = args.get('request',{'type': 'unknown'})

        filename = args.get('subpath',self.index_file) or self.index_file
        if not filename:
            self.log.error(f"{args['client_ip']} - {request.type} - No file name supplied")
            return 400,web.Response(status=400, text=self.error_html(400,'Bad Request'), content_type='text/html')
        filename = os.path.join(self.docpath,filename)
        if not os.path.exists(filename):
            self.log.error(f"{args['client_ip']} - {request.type} - {filename} not found")
            return 404,web.Response(status=404, text=self.error_html(404,"Resource Not Found"), content_type='text/html')
        if os.path.isdir(filename): # If we get a directory, append the indexfile name
            filename = os.path.join(filename,self.index_file)
        try:
            mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            with open(filename,'rb') as f:
                content=f.read()
            if 'text/markdown' in mime:
                mime = 'text/html'
                content = content.decode('utf-8')
                content = self.markdown_to_html(content,os.path.dirname(filename))
                content = content.encode('utf-8')


        except FileNotFoundError as e:
            self.log.error(f"{args['client_ip']} - {request.method} - {filename} not found: {e}")
            code, message = 404, 'Resource Not Found'
        except PermissionError as e:
            self.log.error(f"{args['client_ip']} - {request.method} - {filename} access denied: {e}")
            code, message = 403, 'Permission Denied'
        except OSError as e:
            self.log.error(f"{args['client_ip']} - {request.method} - {filename} OSError: {e}")
            code, message = 400, f"An unexpected OS error occurred: {e}"
        except Exception as e:
            self.log.error(f"{args['client_ip']} - {request.method} - {filename} Unexpected exception: {e}")
            code, message = 400, f"An unexpected error occurred: {e}"
        finally:
            if code != 200:
                response = web.Response(status=code, text=self.error_html(code, message), content_type='text/html')
            else:
                self.log(f"{args['client_ip']} - {filename} {os.path.getsize(filename)} OK")
                response = web.Response(body=content, content_type=mime)
        return code, response