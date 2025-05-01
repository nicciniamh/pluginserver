#!/usr/bin/env python3
"""
plugincore.BasePlugin based plugin for pluginserver

This plugin produces a dictionary and then json object of various
system details, grouped into cpu, ram, disk, network, upgrades, uptime and info

"""
import os
import shutil
import psutil
import socket
from plugincore.baseplugin import BasePlugin
from aiohttp import web

class FSTab:
    """
    A class that holds a list of dicts with filesystem information:
            dev:			Device name 
            friendly_dev:	Friendly name
            mount:			Path on which device is mounted
            fstype:			filesystem type
            options:		filesystem options
            total:			total space in bytes
            free:			free space in bytes
            used:			used space in bytes
            percent:		percent used
    This information is gleaned from /etc/fstab and from shutil
    """
    def __init__(self):
        keys = ['dev','mount','fstype','options']
        self._entries = []
        with open('/etc/fstab') as f:
            for line in f.read().strip().split('\n'):
                line = line.split('#')[0].strip()
                if line:
                    line = line.split()
                    if len(line) != 6:
                        continue
                    dd = {}
                    dd['friendly_dev'] = self._devname(line[0])
                    for i in range(0,len(keys)-1):
                        dd[keys[i]] = line[i]

                    #
                    # as a matter of system information network and virtual filesystems are
                    # filtered out. The idea is to get a list of actual disk devices
                    #
                    if dd['fstype'] in ['ext2','ext3','ext4','fat32','vfat','exfat','fat12','fat16'
                                  'zfs','xfs','ufs','ntfs','apfs','hfs+','hfsplus','hfs','hpfs']:
                        self._get_usage(dd)
                        self._entries.append(dd)
    
    def _get_usage(self,dd:dict) ->None:
        """
        update the dict in dd with the disk usage information
        """
        usage = shutil.disk_usage(dd['mount']) 
        dd.update({
            'total': usage.total,
            'free': usage.free,
            'used': usage.used,
            'percent': 100-int(((usage.free/usage.total)*100))
        })

    def _devname(self,d:str) ->str:
        ''' get a readable name for a fstab device '''
        if '=' in d:
            return d.split('=')[1]
        if 'by-id' in d or 'by-uuid' in d:
            return os.path.basename(os.path.realpath(d))
        return os.path.basename(d)

    def get_fsentry(self,search:str,data:dict) -> dict:
        """
        search through entries where search == data return dict 
        """
        for entry in self._entries:
            for k,v in entry.items():
                if k == search and v == data:
                    return entry
        return None
    
    @property
    def entries(self) -> list:
        """
        return list of file system entry dicts
        """
        return self._entries

class SystemInfo(BasePlugin):
    def __init__(self,**kwargs):
        print("SystemInfo class init to make sure we have the right one 1:53")
        super().__init__(**kwargs)
        self.allowed_fstypes = [    'ext2','ext3','ext4','fat32','vfat','exfat','fat12','fat16'
                                    'zfs','xfs','ufs','ntfs','apfs','hfs+','hfsplus','hfs','hpfs']
        at = kwargs.get('allowed_fstypes')
        if at:
            self.allowed_fstypes = [i.strip() for i in at.split(',')]

    def if_info(self,**data:dict) ->dict:
        if_info = []
        for iface, ifdata in psutil.net_if_addrs().items():
            for i in ifdata:
                if i.family == socket.AddressFamily.AF_INET:
                    mask = sum(bin(int(octet)).count('1') for octet in i.netmask.split('.'))
                    if_info.append({'iface': iface, 'address': f"{i.address}/{mask}"})
        return if_info

    def cpu_info(self, **data:dict) ->dict:
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

    def uptime_info(self, **data:dict)  ->dict:
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

    def disk_info(self,**data:dict) ->dict:
        return FSTab().entries

    def upgrade_info(self,**data:dict) ->dict:
        count = -1;
        try:
            if os.path.exists('/tmp/upgade_packages'):
                with open('/tmp/upgrade_packages') as f:
                    count = int(f.read().strip().split('\n')[0])
        except:
            pass
        return {"Upgradable packages": count}
    
    def os_info(self,**data:dict) ->dict:
        uname = os.uname()
        return {
            'machine': uname.machine,
            'sysname': uname.sysname,
            'version': uname.version,
            'release': uname.release,
            'nodename': uname.nodename,
        }
   

    def ram_info(self,**data:dict) ->dict:    
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
    
    def request_handler(self,**data:dict):
        code = 200
        subpath = data.get('subpath');
        response_data = {
            'net': self.if_info(**data),
            'cpu': self.cpu_info(**data),
            'uptime': self.uptime_info(**data),
            'disk': self.disk_info(**data),
            'upgrades': self.upgrade_info(**data),
            'ram': self.ram_info(**data),
            'info': self.os_info(**data)
        }
        if subpath:
            if subpath in response_data:
                response_data = response_data[subpath]
            else:
                response_data = {'Error': f"{subpath} is not a member of response_data"}
                code = 404;
        return code, response_data
    
if __name__ == "__main__":
    from pprint import pp
    import json
    pp(json.loads(SystemInfo().request_handler().body.decode('ascii')))
