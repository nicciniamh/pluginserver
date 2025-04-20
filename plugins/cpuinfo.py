from plugincore.baseplugin import BasePlugin
import psutil

class CpuInfo(BasePlugin):
    '''
     This is an example plugin for pserv
    '''
    async def handle_request(self, **data):
        return {
            'cpu_count': psutil.cpu_count(),
            'loadavg': psutil.getloadavg(),
            'percent': psutil.cpu_percent(),
            'times': psutil.cpu_times(),
            'stats': psutil.cpu_stats()
        }
