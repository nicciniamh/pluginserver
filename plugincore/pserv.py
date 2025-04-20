#!/usr/bin/env python3
import argparse
import inspect
from aiohttp import web
from plugincore import plugins  # Your plugin system module
from plugincore import config

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-f','--file',default='pserv.ini',type=str, metavar='ini-file',help='Use an alternate config file')
    parser.add_argument('-e','--env-override',default=False, action='store_true', help='Let environment variables override config values')
    parser.add_argument('-p','--prefix',default='PSERV',metavar='string',type=str,help='Use <prefix>_ as prefix for environment variables')

    args = parser.parse_args()

    routes = web.RouteTableDef()
    globalCfg = config.Config(file=args.file,env_override=args.env_override, env_prefix=args.prefix)
    plugin_instances = plugins.get_plugins(globalCfg.paths.plugins,config=globalCfg)
    print(globalCfg.__dict__)
    print(plugin_instances)

    # Dynamically register routes based on plugin ID
    for plugin_id, instance in plugin_instances.items():
        @routes.route('*', f'/{plugin_id}')
        async def handle(request, inst=instance, pid=plugin_id):
            print(request.remote, '- request -', pid)
            data = {}
            if request.method == 'POST' and request.can_read_body:
                try:
                    data.update(await request.json())
                except Exception:
                    pass  # optionally parse form data here too
            data.update(request.query)

            result = await inst.handle_request(**data)

            if isinstance(result, web.StreamResponse):  # already a proper response
                return result
            elif isinstance(result, dict):
                return web.json_response(result)
            elif isinstance(result, str):
                return web.Response(text=result, content_type='text/html')
            else:
                return web.json_response({'result': str(result)})

    # Helper to await if coroutine, else call directly

    async def maybe_async(value):
        return await value if inspect.isawaitable(value) else value

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host=globalCfg.network.bindto, port=globalCfg.network.port)

if __name__ == "__main__":
    main()
