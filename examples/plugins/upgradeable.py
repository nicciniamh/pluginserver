from plugincore.baseplugin import BasePlugin
from aiohttp import web
import subprocess

class Upgradeable(BasePlugin):
    def request_handler(self, **data):

        result = subprocess.run(
            "apt list --upgradable 2>/dev/null | tail -n +2 | wc -l",
            shell=True,
            capture_output=True,
            text=True
        )
    
        count = result.stdout.strip()
        upgradeable = {"Upgradable packages": count}
        response = web.json_response(upgradeable);
        return response;
