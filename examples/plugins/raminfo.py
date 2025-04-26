#!/usr/bin/env python3
from plugincore.baseplugin import BasePlugin
from aiohttp import web
import psutil
import os

class RamInfo(BasePlugin):
	"""
	Plugin to enrmate network interfaces
	"""
	def request_handler(self,**data):
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
