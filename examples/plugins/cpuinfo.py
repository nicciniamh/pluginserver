from plugincore.baseplugin import BasePlugin
from aiohttp import web
import psutil

class CpuInfo(BasePlugin):
    def request_handler(self, **data):
        cpu_model = "Unknown"
        with open('/proc/cpuinfo') as f:
            lines = f.read().strip().split('\n')
        for l in lines:
            if 'model name' in l:
                cpu_model = l.split(':')[1].strip()
        cpudata = {
            'cpu_model': cpu_model,
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq(),
            'loadavg': psutil.getloadavg(),
            'percent': psutil.cpu_percent(),
            'times': psutil.cpu_times(),
            'stats': psutil.cpu_stats()
        }
        key = data.get('key')
        if key:
            if key in cpudata:
                robj = {key: cpudata[key]}
            else:
                return web.json_response({'error': f"key, {key}, not found."}, status=400)
        else:
            robj = cpudata
        
        return web.json_response(robj, status=200)
        
        