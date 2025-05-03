#!/usr/bin/env python3
import argparse
import inspect
import asyncio
import ssl
import os
import sys
import signal
from aiohttp import web
from plugincore import pluginmanager
from plugincore import configfile
import aiohttp_cors
from plugincore.cors import CORS
routes = web.RouteTableDef()
manager = None  # PluginManager reference
globalCfg = None
import aiohttp_cors
from aiohttp import web

corsobj = CORS()
def main():
    global manager
    global globalCfg

    we_are = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    parser = argparse.ArgumentParser(
        description="Plugin Server - create a RESTapi using simple plugins",
        epilog="Nicole Stevens/2025"
        )
    parser.add_argument('-i','--ini-file',default=f"{we_are}.ini",type=str, metavar='ini-file',help='Use an alternate config file')
    args = parser.parse_args()

    signal.signal(signal.SIGHUP, reload)
    print(f"{we_are}({os.getpid()}): Installed SIGHUP handler for reload.")

    globalCfg = configfile.Config(file=args.ini_file)

    ssl_ctx = None
    ssl_cert, ssl_key = (None, None)
    enabled = False

    # SSL setup if enabled
    try:
        ssl_key = globalCfg.SSL.keyfile
        ssl_cert = globalCfg.SSL.certfile
        enabled = globalCfg.SSL.enabled
    except AttributeError:
        pass
    if ssl_key and ssl_cert and enabled:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        print("======== SSL Configuration ========")
        print(f"SSL key {ssl_key}")
        print(f"SSL certificate: {ssl_cert}")
        print(f"SSL context {ssl_ctx}")
        print("Loading SSL cert chain")
        try:
            ssl_ctx.load_cert_chain(ssl_cert, ssl_key, None)
        except Exception as e:
            print(f"Exception({type(e)}): Error loading ssl_cert_chain({ssl_cert},{ssl_key})")
            for p in [ssl_cert, ssl_key]:
                if not os.path.exists(p):
                    print(f"Path: {p} not found.")
            ssl_ctx = None
        print("End of SSL configuration.")

    if not 'paths' in globalCfg:
        print(f"no paths in {globalCfg}")
        sys.exit(1)
    print("======== Loading plugin modules ========")
    manager = pluginmanager.PluginManager(globalCfg.paths.plugins, config=globalCfg)
    manager.load_plugins()

    # Register plugin routes
    for plugin_id, instance in manager.plugins.items():
        register_plugin_route(plugin_id, instance, globalCfg)

    # Setup event loop for file watcher

    # Management endpoints
    register_control_routes(globalCfg)

    app = web.Application()
    
    # CORS setup
    corsobj.setup(app,globalCfg)

    app.add_routes(routes)
    web.run_app(app, host=globalCfg.network.bindto, port=globalCfg.network.port, ssl_context=ssl_ctx)

# --- Auth Helper ---
def check_auth(data, config):
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
    try:
        expected = config.auth.apikey
    except AttributeError:
        return True
    provided = get_token(data) or get_custom_header_token(data) or get_user_token(data)
    #print(f"pserv:check_auth: provided/expected: {provided}/{expected}")
    if not provided:
        print("Returning false")
        return False
    auth_ok = expected == provided
    #print("Returning {auth_ok}")
    return auth_ok

# --- Plugin Request Handler ---
def register_plugin_route(plugin_id, instance, config):
    print(f"Registering route: /{plugin_id} to {instance}")

    @routes.route('*', f'/{plugin_id}')
    @routes.route('*', f'/{plugin_id}/{{tail:.*}}')
    async def handle(request, inst=instance, pid=plugin_id, cfg=config):
        print(request.remote, '- request -', pid)
        plugin = manager.get_plugin(pid)
        data = {}
        if request.method == 'POST' and request.can_read_body:
            try:
                data.update(await request.json())
            except Exception:
                pass
        data.update(request.query)
        data['request_headers'] = dict(request.headers)
        # You can also capture `tail` if you want to use the subpath
        try:
            data['subpath'] = request.match_info['tail']
        except KeyError:
            data['subpath'] = None
        response = await maybe_async(plugin.handle_request(**data))
        response = corsobj.apply_headers(response, request)
        return response

# --- Control Routes ---
def register_control_routes(config):
    print("Registering Control Routes")
    @routes.route('*','/plugins')
    async def plugin_list(request):
        data = {}
        if request.method == 'POST' and request.can_read_body:
            try:
                data.update(await request.json())
            except Exception:
                pass
        data.update(request.query)
        data['request_headers'] = dict(request.headers)
        if not check_auth(data, config):
            return web.json_response({'error': 'unauthorized'}, status=403)
        return corsobj.apply_headers(web.json_response({'loaded_plugins': list(manager.plugins.keys())}),request)

    @routes.route('*','/reload/{plugin_id}')
    async def reload_plugin(request):
        data = {}
        if request.method == 'POST' and request.can_read_body:
            try:
                data.update(await request.json())
            except Exception:
                pass
        data.update(request.query)
        data['request_headers'] = dict(request.headers)
        if not check_auth(data, config):
            return corsobj.apply_headers(web.json_response({'error': 'unauthorized'}, status=403),request)

        pid = request.match_info['plugin_id']
        if pid in manager.plugins:
            success = manager.reload_plugin(pid)
            return corsobj.apply_headers(web.json_response({'reloaded': pid, 'success': success}),request)
        return corsobj.apply_headers(web.json_response({'error': f'Plugin "{pid}" not found'}, status=404),request)

    @routes.route('*', '/reload/all')
    async def reload_all(request):
        data = {}
        if request.method == 'POST' and request.can_read_body:
            try:
                data.update(await request.json())
            except Exception:
                pass
        data.update(request.query)
        data['request_headers'] = dict(request.headers)
        if not check_auth(data, config):
            return corsobj.apply_headers(web.json_response({'error': 'unauthorized'}, status=403),request)
        manager.load_plugins()
        return corsobj.apply_headers(web.json_response({'status': 'All plugins reloaded', 'loaded_plugins': list(manager.plugins.keys())}),request)

# --- Coroutine Await Helper ---
async def maybe_async(value):
    return await value if inspect.isawaitable(value) else value

# ---- Reload handler ----
def reload(signum, frame):
    print("Received SIGHUP, restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    main()
