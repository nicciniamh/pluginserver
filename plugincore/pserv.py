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
from plugincore import config
import aiohttp_cors

routes = web.RouteTableDef()
manager = None  # PluginManager reference
globalCfg = None

class CORS:
	def setup(self,app,config):
		self.cors_enabled = False
		self.config = config
		self.cors_enabled = config.cors.enabled in ['true','enabled','on','1','enable']
		if self.cors_enabled:
			cors_origin_url = config.cors.origin_url
			print(f"CORS Setup - ORIGIN URL is {config.cors.origin_url}")
			cors = aiohttp_cors.setup(app)

			# Allow specific origin for all routes
			self.cors_enbled = True
			for route in list(app.router.routes()):
				cors.add(route, {
					"origins": [
						cors_origin_url
					],
					"allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
					"allow_methods": ["GET", "POST", "OPTIONS"]
				})
		return self
	def _add_header(self,response):
		try:
			if self.cors_enabled:
				response.headers['Access-Control-Allow-Origin'] = self.config.cors.origin_url
				response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
				response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
		except AttributeError as e:
			print(f"Exception(AttributeError) this probably means our corsobj is screwed up: {e}")
		return response

	def apply_headers(self,response):
		if isinstance(response,web.StreamResponse):
			response = self._add_header(response)
		elif isinstance(response, dict):
			response = self._add_header(web.json_response(response))
			return response
		elif isinstance(response, str):
			response = self._add_header(web.Response(text=response, content_type='text/html'))
		else:
			response = self._add_header(web.json_response({'result': str(response)}))
		return response

corsobj = CORS()
def main():
	global manager
	global globalCfg
#	global corsobj
	# Reload handler
	we_are = os.path.splitext(os.path.basename(sys.argv[0]))[0]

	parser = argparse.ArgumentParser(
		description="Plugin Server - create a RESTapi using simple plugins",
		epilog="Nicole Stevens/2025"
		)
	parser.add_argument('-f','--file',default='pserv.ini',type=str, metavar='ini-file',help='Use an alternate config file')
	parser.add_argument('-e','--env-override',default=False, action='store_true', help='Let environment variables override config values')
	parser.add_argument('-p','--prefix',default='PSERV',metavar='string',type=str,help='Use <prefix>_ as prefix for environment variables')
	parser.add_argument('--ssl-key',default=None,metavar='key-file',help='use key-file for SSL key')
	parser.add_argument('--ssl-cert',default=None,metavar='cert-file',help='use key-file for SSL certificate')
	args = parser.parse_args()

	signal.signal(signal.SIGHUP, reload)
	print(f"{we_are}({os.getpid()}): Installed SIGHUP handler for reload.")

	globalCfg = config.Config(file=args.file, env_override=args.env_override, env_prefix=args.prefix)

	ssl_ctx = None
	ssl_cert, ssl_key = (None, None)
	enabled = False

	if args.ssl_key and args.ssl_cert:
		ssl_key = args.ssl_key
		ssl_cert = args.ssl_cert
		enabled = True
	else:
		# SSL setup if enabled
		try:
			ssl_key = globalCfg.SSL.keyfile
			ssl_cert = globalCfg.SSL.certfile
			enabled = globalCfg.SSL.enabled.lower() == 'true'
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
	web.run_app(app, host=globalCfg.network.bindto, port=int(globalCfg.network.port), ssl_context=ssl_ctx)

# --- Auth Helper ---
def check_auth(data, config):
	try:
		expected = config.auth.apikey
	except AttributeError:
		expected = None
	provided = data.get('apikey')
	return expected and provided and expected == provided

# --- Plugin Request Handler ---
def register_plugin_route(plugin_id, instance, config):
	print(f"Registering route: /{plugin_id} to {instance}")

	@routes.route('*', f'/{plugin_id}')
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

		response = await maybe_async(plugin.handle_request(**data))
		return corsobj.apply_headers(response)
		

# --- Control Routes ---
def register_control_routes(config):
	@routes.get('/plugins')
	async def plugin_list(request):
		data = dict(request.query)
		if not check_auth(data, config):
			return web.json_response({'error': 'unauthorized'}, status=403)
		return corsobj.apply_headers(web.json_response({'loaded_plugins': list(manager.plugins.keys())}))

	@routes.get('/reload/{plugin_id}')
	async def reload_plugin(request):
		data = dict(request.query)
		if not check_auth(data, config):
			return corsobj.apply_headers(web.json_response({'error': 'unauthorized'}, status=403))

		pid = request.match_info['plugin_id']
		if pid in manager.plugins:
			success = manager.reload_plugin(pid)
			return corsobj.apply_headers(web.json_response({'reloaded': pid, 'success': success}))
		return corsobj.apply_headers(web.json_response({'error': f'Plugin "{pid}" not found'}, status=404))

	@routes.get('/reload/all')
	async def reload_all(request):
		data = dict(request.query)
		if not check_auth(data, config):
			return corsobj.apply_headers(web.json_response({'error': 'unauthorized'}, status=403))
		manager.load_plugins()
		return corsobj.apply_headers(web.json_response({'status': 'All plugins reloaded', 'loaded_plugins': list(manager.plugins.keys())}))

# --- Coroutine Await Helper ---
async def maybe_async(value):
	return await value if inspect.isawaitable(value) else value

# ---- Reload handler ----
def reload(signum, frame):
	print("Received SIGHUP, restarting...")
	os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
	main()
