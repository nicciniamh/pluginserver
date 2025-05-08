import time
import os
import mimetypes
import re
from plugincore.baseplugin import BasePlugin
from aiohttp import web
from bs4 import BeautifulSoup
import markdown

class ServeFiles(BasePlugin):
    """
    This plugin serves files. See the config document for setting up serving of files, 
    this plugin must be present for file serving to work.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.highlight_css = 'highlight.css'
        self.markdown_css = 'markdown.css'
        self.log_file = None
        if not 'file_server' in self.config:
            raise AttributeError("Cannot find 'file_server' in config.")
        if 'common_log' in self.config.file_server:
            self.log_file = os.path.expanduser(self.config.file_server.common_log)
            self.log(f"Serve access log is {self.log_file}")
        for k in ['highlight','markdown']:
            if f"{k}_css" in self.config.file_server:
                css = self.config.file_server.get(f"{k}_css",f"{k}.css") or f"{k}.css"
                setattr(self,f"{k}_css",css)
        self.index_file = self.config.file_server.get('indexfile','index.html') or 'index.html'
        self.log(f"{type(self)}: index_file is {self.index_file}")
        self.log(f"{type(self)}: markdown_css is {self.markdown_css}")
        self.log(f"{type(self)}: highlight_css is {self.highlight_css}")
        if 'documents' in self.config.file_server:
            if ':' in self.config.file_server.documents:
                rpath, dpath = self.config.file_server.documents.split(':',1)
            else:
                rpath, dpath = os.path.basename(self.config.file_server.documents), self.config.file_server.documents
        else:
            raise AttributeError('File service is not configured in the configuraiton file.')
        self._plugin_id = rpath
        self.docpath = dpath

    def retitle_document(self, text, title):
        soup = BeautifulSoup(text, "html.parser")
        print(f"Setting document title to {title}")
        # Modify existing title
        if soup.title:
            soup.title.string = title
        else:
            # Create a <title> tag if it doesn't exist
            new_title = soup.new_tag("title")
            new_title.string = title
            if soup.head:
                soup.head.append(new_title)
            else:
                new_head = soup.new_tag("head")
                new_head.append(new_title)
                soup.html.insert(0, new_head)
        return str(soup)


    def error_html(self,code,message):
        return f"""<html>
            <head>
                <title>{message}</title>
            </head>
            <body>
                <h1>{code} - {message}</h1>
            </body>
        </html>"""

    def preprocess(self, text, basepath):
        title = ""
        byte_data = False
        if isinstance(text,bytes):
            byte_data = True
            text = text.decode('utf-8')   

        def replacer(match):
            nonlocal title
            tag = match.group(1)
            value = match.group(2)

            handler = processors.get(f"@{tag}")
            if handler:
                return handler(value)
            return match.group(0)

        def include_file(name):
            nonlocal basepath
            name = os.path.expanduser(name)
            filename = os.path.join(basepath, name) if not os.path.isabs(name) else name
            mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            try:
                with open(filename) as f:
                    text = f.read()
            except Exception as e:
                self.log.error(f"{type(e)} including file {filename}")
                return ""
            if 'markdown' in mime:
                text = self.markdown_to_html(text,basepath)
            return text

        def set_title(new_title):
            self.log(f"New document title {new_title}")
            nonlocal title
            title = new_title
            return ''
        
        def cloctime(format):
            if not format.startswith('+'):
                format = format[1:]
            else:
                format = '%T'
            return time.strftime(format, time.localtime(time.time()))
        
        def file_date_time(info):
            nonlocal basepath
            filename,format = info.split('+',1)
            filename = os.path.join(basepath, filename) if not os.path.isabs(filename) else filename
            try:
                st = os.stat(filename)
            except Exception as e:
                self.log.error(f"{type(e)}: file_data_time: Couln't stat {filename}")
                return ""
            if not format:
                format = '%T %D'
            return time.strftime(format,time.localtime(st.st_mtime))

        processors = {
            '@INCLUDE': include_file,
            '@TITLE': set_title,
            '@FILETIME': file_date_time,
            '@TIME': cloctime
        }

        # Match e.g. @TITLE=SomeTitle/ or @INCLUDE=path/to/file
        pattern = r'@([A-Za-z]+)=([^@]+)@'
        text = re.sub(pattern, replacer, text)
        if byte_data:
            return title, text.encode('utf-8')
        return title, text
    
    def markdown_to_html(self, text, basepath):
        byte_data = False
        if isinstance(text,bytes):
            byte_data = True
            text = text.decode('utf-8')   

        title, text = self.preprocess(text,basepath)
        mdhtml = markdown.markdown(text, extensions=['fenced_code', 'codehilite'])

        mdhtml = f"""<!DOCTYPE html>
            <html>
            <head>
                <title></title>
                <link rel="stylesheet" href="{self.markdown_css}">
                <link rel="stylesheet" href="{self.highlight_css}">
            </head>
            <body>
            {mdhtml}
            </body>
            </html>"""
        if byte_data:
            return mdhtml.encode('utf-8')
        return self.retitle_document(mdhtml,title)

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

        mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        try:
            base_path = os.path.dirname(filename)
            with open(filename,'rb') as f:
                content=f.read()
            if 'text/markdown' in mime:
                mime = 'text/html'
                content = self.markdown_to_html(content,base_path)
            if 'text/html' in mime:
                title, content = self.preprocess(content,base_path)
                if title:
                    self.retitle_document(content,title)
                if not isinstance(content,bytes):
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
                #self.log(f"{args['client_ip']} - {filename} {os.path.getsize(filename)} OK")
                print(self.log.common_log(
                    ip=args['client_ip'],
                    path=filename,
                    size=os.path.getsize(filename),
                    method = args['request'].method,
                    protocol = 'HTTPS' if 'SSL' in self.config else 'HTTP',
                    status='OK',file=self.log_file))
                response = web.Response(body=content, content_type=mime)
        return code, response