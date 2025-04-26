#!/usr/bin/env python3
from plugincore.baseplugin import BasePlugin
from aiohttp import web
import psutil
import os
import sys
import shutil
from plugincore.baseplugin import BasePlugin
from aiohttp import web
import psutil
import socket
import subprocess

class SystemInfo(BasePlugin):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.allowed_fstypes = [    'ext2','ext3','ext4','fat32','vfat','exfat','fat12','fat16'
                                    'zfs','xfs','ufs','ntfs','apfs','hfs+','hfsplus','hfs','hpfs']
        at = kwargs.get('allowed_fstypes')
        if at:
            self.allowed_fstypes = [i.strip() for i in at.split(',')]

    def if_info(self,**data):
        if_info = []
        for iface, ifdata in psutil.net_if_addrs().items():
            for i in ifdata:
                if i.family == socket.AddressFamily.AF_INET:
                    mask = sum(bin(int(octet)).count('1') for octet in i.netmask.split('.'))
                    if_info.append({'iface': iface, 'address': f"{i.address}/{mask}"})
        return if_info

    def cpu_info(self, **data):
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
        return cpudata

    def uptime_info(self, **data):
        '''
        Get uptime as seconds, pretty and boot time 
        '''
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])

        minutes, seconds = divmod(int(uptime_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 7)

        parts = []
        if weeks:
            parts.append(f"{weeks} week{'s' if weeks != 1 else ''}")
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        
        if not parts:
            parts.append("less than a minute")

        pretty =  "up " + ", ".join(parts)

        return  {'pretty': pretty, 'seconds': seconds}

    def disk_info(self,**data):
        at = data.get('types')
        if at:
            at = [i.strip() for i in at.split(',')]
        else:
            at = self.allowed_fstypes
        return self.get_disk_entries(at)

    def get_disk_entries(self, allowed_types):
        """
        This method does the heavy lifting examining file systems and builds a list of dicts 
        containing information about each filesystem. 
        """

        entries = []

        def _devname(d):
            ''' get a readable name for a fstab device '''
            if '=' in d:
                return d.split('=')[1]
            if 'by-id' in d or 'by-uuid' in d:
                return os.path.basename(os.path.realpath(d))
            return os.path.basename(d)

        with open('/etc/fstab') as f:
            for l in f.read().strip().split('\n'):
                l = l.strip()
                if not len(l) or l.startswith(' ') or l.startswith('#'):
                    continue
                try:
                    dev,mpoint,fstype,options,freq,passno = l.split()
                except:
                    print(f'Cannot parse line "{l}',file=sys.stderr)
                    continue
                try:
                    if fstype in allowed_types:
                        if mpoint and os.path.exists(mpoint):
                            usage = shutil.disk_usage(mpoint)
                            entries.append({
                                'dev': dev,
                                'friendly_dev': _devname(dev),
                                'fstype': fstype,
                                'mpoint':mpoint,
                                'options': options,
                                'total': usage.total,
                                'free': usage.free,
                                'used': usage.used,
                            })
                except ValueError:
                    pass
        return entries

    def upgrade_info(self,**data):
        count = -1;
        try:
            if os.path.exists('/tmp/upgade_packages'):
                with open('/tmp/upgrade_packages') as f:
                    count = int(f.read().strip().split('\n')[0])
        except:
            pass
        return {"Upgradable packages": count}
    
    def os_info(self,**data):
        uname = os.uname()
        return {
            'machine': uname.machine,
            'sysname': uname.sysname,
            'version': uname.version,
            'release': uname.release,
            'nodename': uname.nodename,
        }
   

    def ram_info(self,**data):    
        ram = psutil.virtual_memory()
        return {
			'total': ram.total,
			'free':  ram.free,
			'used': ram.used,
			'free': ram.free,
			'cached': ram.cached,
			'percent': ram.percent,
			'active': ram.active,
			'buffers': ram.buffers,
			'inactive': ram.inactive,
			'active': ram.active,
			'shared': ram.shared,
			'slab': ram.slab
		}
    
    def request_handler(self,**data):
        data = {
            'net': self.if_info(**data),
            'cpu': self.cpu_info(**data),
            'uptime': self.uptime_info(**data),
            'disk': self.disk_info(**data),
            'upgrades': self.upgrade_info(**data),
            'ram': self.ram_info(**data),
            'info': self.os_info(**data)
        }

        response = web.json_response(data);
        return response;

if __name__ == "__main__":
    from pprint import pp
    import json
    pp(json.loads(SystemInfo().request_handler().body.decode('ascii')))