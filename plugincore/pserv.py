#!/usr/bin/env python3
import argparse
import inspect
import asyncio
import ssl
import os
import sys
import signal
import aiohttp_cors
from aiohttp import web
from plugincore import pluginmanager
from plugincore import configfile
from plugincore import logjam

routes = web.RouteTableDef()
manager = None
globalCfg = None
config_file = None

async_tasks = []

log = print

globals()['_signal_exit_code'] = 0

def cors_setup(app):
    global globalCfg
    global log
    if 'cors' in globalCfg and 'enabled' in globalCfg['cors']:
        rules = aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=("Content-Type", "Authorization", "X-Requested-With", "Accept"),
            expose_headers=("X-Custom-Header", "Content-Length"),
            max_age=3600
        )

        settings = {}
        for origin in globalCfg.cors.origin_url:
            settings[origin] = rules

        cors_configuration = aiohttp_cors.setup(app, defaults=settings)
        
        for route in list(app.router.routes()):
            cors_configuration.add(route)
            
        log.info('CORS middleware enabled')

def register_async_task(task):
    global async_tasks
    async_tasks.append(task)

def get_signal_name(signal_number):
    for name in dir(signal):
        if name.startswith("SIG") and getattr(signal, name) == signal_number:
            return name
    return None

on_shutdown_entered = False
async def on_shutdown(*args):
    global on_shutdown_entered
    global manager
    global async_tasks
    global log
    global globalCfg
    if 'pidfile' in globalCfg.paths:
        try:
            os.unlink(globalCfg.paths.pidfile)
        except:
            pass
    if on_shutdown_entered:
        return
    on_shutdown_entered = True
    log(("Sending plugins the terminate signal"))
    for id, plugin in manager.plugins.items():
        try:
            log(f"Terminating plugin {id}")
            plugin.terminate_plugin()
            await asyncio.sleep(1)
        except Exception as e:
            log(f"{type(e).__name__} Exception unloading plugin id {id}: {e}")
    else:
        log("Plugin manager or plugins not available for shutdown.")

    #await asyncio.sleep(max(len(all_current_tasks)+1,5))
    log("Waiting for terminate_plugins to complete.")
    all_current_tasks = asyncio.all_tasks()
    log.info(f"Ensuring tasks are ended")
    current_shutdown_task = asyncio.current_task()

    tasks_to_cancel = []
    for task in all_current_tasks:
        if task is not current_shutdown_task:
            if task.get_name() != '::main::':
                tasks_to_cancel.append(task)

    if tasks_to_cancel:
        for task_to_cancel_item in tasks_to_cancel:
            if not task_to_cancel_item.done():
                log(f"terminating task {task_to_cancel_item.get_name()}")
                task_to_cancel_item.cancel()
        log("Waiting for all other async tasks to complete cancellation...")
        results = await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
        for i, result in enumerate(results):
            task = tasks_to_cancel[i]
            task_name = task.get_name() if hasattr(task, 'get_name') else f"Task-{id(task)}"
            if isinstance(result, asyncio.CancelledError):
                log(f"{task_name} was successfully cancelled.")
            elif isinstance(result, Exception):
                log(f"{task_name} finished with an exception: {type(result).__name__} - {result}")
            else:
                log(f"{task_name} finished. Result: {result}")
    else:
        log("No other async tasks found to cancel.")

async def _sh_then_act(action_func, *action_args):
    global log
    try:
        await on_shutdown()
    except Exception as e:
        current_log_func = log if callable(getattr(log, 'exception', None)) else lambda msg: print(msg, file=sys.stderr)
        current_log_func(f"Exception during on_shutdown from signal: {type(e).__name__} - {e}")
    finally:
        if callable(action_func):
            action_func(*action_args)

def _sched_sh(async_wrapper_func, sync_action_func, *sync_action_args):
    global log
    current_log_func = log if callable(getattr(log, 'info', None)) else print
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.create_task(async_wrapper_func(sync_action_func, *sync_action_args))
        else:
            if callable(sync_action_func):
                sync_action_func(*sync_action_args)
    except RuntimeError:
        if callable(sync_action_func):
            sync_action_func(*sync_action_args)
    except Exception as e:
        current_log_func(f"Error in _sched_sh: {type(e).__name__} - {e}")
        if callable(sync_action_func): 
             sync_action_func(*sync_action_args)

def _act_execl():
    global log
    sys.stdout.flush()
    sys.stderr.flush()
    os.execl(sys.executable, sys.executable, *sys.argv)

def _act_exit(exit_code):
    globals()['_signal_exit_code'] = exit_code
    try:
        asyncio.get_running_loop().stop()
    except RuntimeError:
        sys.exit(exit_code)

async def pserve_main(args):
    global log
    global manager
    global globalCfg
    global config_file
    global routes
    global on_shutdown
    asyncio.current_task().set_name("::main::")

    we_are = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    config_file = args.ini_file
    if args.log:
        log = logjam.LogJam(file=args.log, name=we_are,level=args.level)
    else:
        log = logjam.LogJam(name=we_are)

    signal.signal(signal.SIGUSR1, reload)
    log(f"{we_are}({os.getpid()}): Installed SIGUSR1 handler for reload.")
    for sig_val_item in []:
        try:
            signal.signal(sig_val_item, lambda signum_val, frame_val: terminate(signum_val, frame_val, sig_to_exit_code=signum_val))
            log(f"Installed signal handler for {get_signal_name(sig_val_item)} to terminate wrapper")
        except Exception as e:
            log(f"{type(e).__name__} setting signal handler for {sig_val_item}: {e}")

    globalCfg = configfile.Config(file=config_file)
    if 'pidfile' in globalCfg.paths:
        with open(globalCfg.paths.pidfile,'w') as f:
            print(f"{os.getpid()}",file=f)
    ssl_ctx = None
    ssl_cert, ssl_key = (None, None)
    enabled = False

    try:
        ssl_key = globalCfg.SSL.keyfile
        ssl_cert = globalCfg.SSL.certfile
        enabled = globalCfg.SSL.enabled
    except AttributeError:
        pass

    if ssl_key and ssl_cert and enabled:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        log("======== SSL Configuration ========")
        log(f"SSL key {ssl_key}")
        log(f"SSL certificate: {ssl_cert}")
        try:
            ssl_ctx.load_cert_chain(ssl_cert, ssl_key, None)
            log(f"SSL context loaded with cert: {ssl_cert}, key: {ssl_key}")
        except FileNotFoundError as e:
            log(f"FileNotFoundError loading SSL cert/key: {e}. Check paths: Cert='{ssl_cert}', Key='{ssl_key}'")
            ssl_ctx = None
        except ssl.SSLError as e:
            log(f"ssl.SSLError loading SSL cert/key: {e}. Plese check your key and certfiles.")
            ssl_ctx = None
        except Exception as e:
            log(f"Exception({type(e).__name__}): Error loading ssl_cert_chain: {e}")
            ssl_ctx = None
        log("End of SSL configuration.")
    elif enabled:
        log("SSL is enabled in config, but certfile or keyfile is missing/not specified.")

    if not 'paths' in globalCfg or  not 'plugins' in globalCfg.paths:
        log(f"Configuration error: 'paths.plugins' not found in '{config_file}'. Cannot load plugins.")
        sys.exit(1)
    log("======== Loading plugin modules ========")
    manager = pluginmanager.PluginManager(globalCfg.paths.plugins, config=globalCfg, log=log, task_callback=register_async_task, args=args)
    await manager.load_plugins()

    for plugin_id, instance in manager.plugins.items():
        register_plugin_route(plugin_id, instance, globalCfg)

    register_control_routes(globalCfg)

    app = web.Application()
    app.add_routes(routes)
    app.on_shutdown.append(on_shutdown)
    cors_setup(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=globalCfg.network.bindto, port=globalCfg.network.port, ssl_context=ssl_ctx)

    try:
        await site.start()
        log(f"Server started on {globalCfg.network.bindto}:{globalCfg.network.port}")
        await asyncio.Event().wait()
    except OSError as e:
        log.error(e)
        sys.exit(1)
    except (KeyboardInterrupt, asyncio.CancelledError) as e:
        log(f"Exception({type(e).__name__}). Initiating shutdown.")
        pass
    except Exception as e:
        log.exception(f"{type(e)}: Unexpected error in pserve_main server loop: {e}")
    finally:
        await runner.cleanup()

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
    if not expected:
        return True

    provided = get_token(data) or get_custom_header_token(data) or get_user_token(data)
    if not provided:
        return False
    auth_ok = expected == provided
    return auth_ok

def register_plugin_route(plugin_id, instance, config):
    global log
    global manager
    global routes

    log(f"Registering route: /{plugin_id}")

    @routes.route('GET', f'/{plugin_id}')
    @routes.route('GET', f'/{plugin_id}/{{tail:.*}}')
    @routes.route('POST', f'/{plugin_id}')
    @routes.route('POST', f'/{plugin_id}/{{tail:.*}}')
    async def handle(request, inst=instance, pid=plugin_id, cfg=config):
        plugin = await manager.get_plugin(pid)
        if plugin is None:
            log(f"Plugin {pid} not found for request.")
            return web.json_response({"error": f"Plugin {pid} not found"}, status=404)

        data = {'log': log, 'request_headers': dict(request.headers), 'request': request}
        if request.method == 'POST' and request.can_read_body:
            try:
                rqj = await request.json()
                data.update(rqj)
            except Exception as e:
                log.exception(f"Cannot get request body for plugin {pid}: {e}")
        data.update(request.query)
        try:
            data['subpath'] = request.match_info.get('tail')
        except KeyError:
            data['subpath'] = None

        response_data = await maybe_async(inst.handle_request(**data))

        if not isinstance(response_data, web.StreamResponse):
            if isinstance(response_data, (dict, list)):
                response = web.json_response(response_data)
            elif isinstance(response_data, str):
                response = web.Response(text=response_data)
            else:
                log(f"Plugin {pid} returned unexpected response type: {type(response_data)}")
                response = web.json_response({"error": "Internal server error from plugin response"}, status=500)
        else:
            response = response_data
        return response

def register_control_routes(config):
    global log
    global manager
    global globalCfg
    global config_file
    global routes

    log("Registering Control Routes")
    @routes.route('GET','/plugins')
    @routes.route('POS','/plugins')
    async def plugin_list(request):
        data = {}
        if request.method == 'POST' and request.can_read_body:
            try:
                data.update(await request.json())
            except Exception: pass
        data.update(request.query)
        data['request_headers'] = dict(request.headers)
        if not check_auth(data, config):
            return web.json_response({'error': 'unauthorized'}, status=403)
        
        loaded_plugins = list(manager.plugins.keys()) if manager and manager.plugins else []
        return web.json_response({'loaded_plugins': loaded_plugins})


    @routes.route('GET','/reload/{plugin_id}')
    @routes.route('POST','/reload/{plugin_id}')
    async def reload_plugin(request):
        current_config_for_auth = globalCfg

        data = {}
        if request.method == 'POST' and request.can_read_body:
            try: data.update(await request.json())
            except Exception: pass
        data.update(request.query)
        data['request_headers'] = dict(request.headers)
        if not check_auth(data, current_config_for_auth):
            return web.json_response({'error': 'unauthorized'}, status=403)

        pid = request.match_info['plugin_id']
        if manager and pid in manager.plugins:
            try:
                reloaded_cfg = configfile.Config(file=config_file)
                globals()['globalCfg'] = reloaded_cfg
                manager.reset_config(reloaded_cfg)
                success = await manager.reload_plugin(pid)
                web.json_response({'reloaded': pid, 'success': success})
            except Exception as e:
                log.exception(f"Error reloading plugin {pid}: {e}")
                return web.json_response({'error': f'Failed to reload plugin {pid}'}, status=500)
        web.json_response({'error': f'Plugin "{pid}" not found'}, status=404)

    @routes.route('GET', '/reload/all')
    @routes.route('POST', '/reload/all')
    async def reload_all(request):
        current_config_for_auth = globalCfg

        data = {}
        if request.method == 'POST' and request.can_read_body:
            try: data.update(await request.json())
            except Exception: pass
        data.update(request.query)
        data['request_headers'] = dict(request.headers)
        if not check_auth(data, current_config_for_auth):
            return web.json_response({'error': 'unauthorized'}, status=403)
        
        try:
            reloaded_cfg = configfile.Config(file=config_file)
            globals()['globalCfg'] = reloaded_cfg
            if manager:
                manager.reset_config(reloaded_cfg)
                await manager.load_plugins()
                return web.json_response({'status': 'All plugins reloaded', 'loaded_plugins': list(manager.plugins.keys())})
            else:
                return web.json_response({'error': 'Plugin manager not available'}, status=500)
        except Exception as e:
            log.exception(f"Error reloading all plugins: {e}")
            return web.json_response({'error': 'Failed to reload all plugins'}, status=500)

async def maybe_async(value):
    return await value if inspect.isawaitable(value) else value

def reload(signum, frame):
    global log
    log(f"Received {get_signal_name(signum)} - Terminating plugins")
    _sched_sh(_sh_then_act, _act_execl)

def terminate(signum, frame, sig_to_exit_code=None):
    global log
    actual_exit_code = sig_to_exit_code if sig_to_exit_code is not None else signum
    log(f"Received {get_signal_name(signum)} - Terminating plugins")
    _sched_sh(_sh_then_act, _act_exit, actual_exit_code)

def main():
    global log
    global _signal_exit_code

    we_are = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    parser = argparse.ArgumentParser(
        description="Plugin Server - create a RESTapi using simple plugins",
        epilog="Nicole Stevens/2025"
        )
    parser.add_argument('-i','--ini-file',default=f"{we_are}.ini",type=str, metavar='ini-file',help='Use an alternate config file')
    parser.add_argument('-l','--log',default=None,type=str,metavar='file',help='Set a log file')
    parser.add_argument('-v','--level',default='DEBUG',type=str,help="Logging level, INFO DEBUG ERROR CRITICAL", metavar='level')
    args = parser.parse_args()

    exit_code = 0
    _signal_exit_code = 0

    try:
        asyncio.run(pserve_main(args))
        exit_code = _signal_exit_code
    except KeyboardInterrupt:
        log.info("Application terminated by KeyboardInterrupt (caught in main).")
        exit_code = getattr(signal.SIGINT, 'value', 2)
    except SystemExit as e:
        log.info(f"SystemExit caught in main with code: {e.code}")
        exit_code = e.code if e.code is not None else 0
    except Exception as e:
        log.exception(f"Unhandled exception in main: {e}")
        exit_code = 1
    finally:
        log.info(f"Application exiting with code {exit_code}.")

    sys.exit(exit_code)
    
if __name__ == "__main__":
    main()