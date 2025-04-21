#!/usr/bin/env python3
from plugincore.baseplugin import BasePlugin
from aiohttp import web
import shutil
import sys
import os


class DiskInfo(BasePlugin):
    """
    This class is a more complicated example of a plugin. 
    Here we we have a constructor (__init__) that initializes with the superclass, 
    BasePlugin, and sets some class specific parameters. 
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.allowed_fstypes = ['ext2','ext3','ext4','fat32','vfat','exfat','fat12','fat16'
                                  'zfs','xfs','ufs','ntfs','apfs','hfs+','hfsplus','hfs','hpfs']
        at = kwargs.get('allowed_fstypes')
        if at:
            self.allowed_fstypes = [i.strip() for i in at.split(',')]
        
    def request_handler(self, **data):
        """
        Check to see if the types parameter was sent and decode it to a list
        otherwise use the instance variablet allowed_types to pass to _get_entries.
        Only file system types listed in at will be returned. 
        """
        at = data.get('types')
        if at:
            at = [i.strip() for i in at.split(',')]
        else:
            at = self.allowed_fstypes
        return self._get_entries(at)

    def _get_entries(self, allowed_types):
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
                                'friendlt_dev': _devname(dev),
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