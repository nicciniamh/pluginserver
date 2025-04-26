from plugincore.baseplugin import BasePlugin
from aiohttp import web
import subprocess

class Uptime(BasePlugin):
    def request_handler(self, **data):
        '''
        Get uptime as seconds, pretty and boot time 
        '''
        result = subprocess.run(
            "/bin/uptime -p",
            shell=True,
            capture_output=True,
            text=True
        )
        uptime = result.stdout.strip()
        result = subprocess.run(
            "/bin/uptime --since",
            shell=True,
            capture_output=True,
            text=True
        )
        with open('/proc/uptime') as f:
            seconds = float(f.read().split()[0])
        boot = result.stdout.strip()
        data = {'pretty': uptime, 'boot_time': boot, 'seconds': seconds}
        response = web.json_response(data)
        return response;
