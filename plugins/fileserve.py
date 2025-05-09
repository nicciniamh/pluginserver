import time
import os
import mimetypes
import re
from plugincore.baseplugin import BasePlugin
from aiohttp import web
from bs4 import BeautifulSoup
import markdown
import aiofiles

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

        self.log_includes = self.config.file_server.get('log_includes',False) or False
        if self.log_includes:
            self.log('Magic includes are logged')        
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
        dpath=os.path.expanduser(dpath)
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

    async def preprocess(self, text, basepath, **args):
        title = ""
        if isinstance(text,bytes):
            text = text.decode('utf-8')   

        async def run_async_replacer(text,pattern):
            output = []
            last_end = 0
            for match in re.finditer(pattern, text):
                output.append(text[last_end:match.start()])
                replacement = await replacer(match)
                output.append(replacement)
                last_end = match.end()
            output.append(text[last_end:])
            return ''.join(output)


        async def replacer(match):
            nonlocal title
            tag = match.group(1)
            value = match.group(2)

            handler = processors.get(f"@{tag}")
            if handler:
                return await handler(value)
            return match.group(0)

        async def include_file(name):
            nonlocal basepath
            nonlocal args
            text = ""
            name = os.path.expanduser(name)
            filename = os.path.join(basepath, name) if not os.path.isabs(name) else name
            mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            try:
                async with aiofiles.open(filename) as f:
                    text = await f.read()
                    _, text = await self.preprocess(text,basepath,**args)
                    self.log.debug(f"include file {filename} clf is {self.log_includes}")
                    if self.log_includes:
                        self.log.common_log(
                            ip=args.get('client_ip','system') or 'system',
                            path=filename,
                            size=len(text),
                            method = "include",
                            protocol = "file",
                            status='OK',file=self.log_file)

            except Exception as e:
                message = f"{type(e)} including file {filename}: {e}"
                self.log.exception(message)
                return message
            if 'markdown' in mime:
                text = self.markdown_to_html(text,basepath)
            return text

        async def set_title(new_title):
            self.log(f"New document title {new_title}")
            nonlocal title
            title = new_title
            return ''
        
        async def cloctime(format):
            if not format.startswith('+'):
                format = format[1:]
            else:
                format = '%T'
            return time.strftime(format, time.localtime(time.time()))
        
        async def file_date_time(info):
            nonlocal basepath
            filename,format = info.split('+',1)
            filename = os.path.join(basepath, filename) if not os.path.isabs(filename) else filename
            try:
                st = os.stat(filename)
            except Exception as e:
                self.log.error(f"{type(e)}: file_data_time: Coulnd't stat {filename}")
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

        pattern = r'(?<!\\)@([A-Za-z]+)=([^@]+)@'
        text = await run_async_replacer(text,pattern)
        text = re.sub(r'\\(@[A-Za-z]+=[^@]+@)', r'\1', text)
        return title, text
    
    def markdown_to_html(self, text,title=""):
        if isinstance(text,bytes):
            text = text.decode('utf-8')   

        mdhtml = markdown.markdown(text, extensions=['fenced_code', 'tables','codehilite'])

        mdhtml = f"""<!DOCTYPE html>
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
        return mdhtml

    async def request_handler(self, **args):
        code, message, title = 200, '', ''
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
            async with aiofiles.open(filename,'rb') as f:
                content = await f.read()
            if 'text/markdown' in mime:
                mime = 'text/html'
                title, content = await self.preprocess(content,base_path,**args)
                content = self.markdown_to_html(content,title)
            elif 'text/html' in mime:
                title, content = await self.preprocess(content,base_path,**args)
            if title:
                content = self.retitle_document(content,title)
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
                self.log.common_log(
                    ip=args['client_ip'],
                    path=filename,
                    size=len(content),
                    method = args['request'].method,
                    protocol = 'HTTPS' if 'SSL' in self.config else 'HTTP',
                    status='OK',file=self.log_file)
                response = web.Response(body=content, content_type=mime)
        return code, response