#!/usr/bin/env python3
from plugincore.baseplugin import BasePlugin
from aiohttp import web
import psutil
import socket
import os

class IFInfo(BasePlugin):
	"""
	Plugin to enrmate network interfaces
	"""
	def request_handler(self,**data):
		if_info = [{'ifinfo': 'v0.0.1'}]
		for iface, ifdata in psutil.net_if_addrs().items():
			for i in ifdata:
				if i.family == socket.AddressFamily.AF_INET:
					mask = sum(bin(int(octet)).count('1') for octet in i.netmask.split('.'))
					if_info.append({'iface': iface, 'address': f"{i.address}/{mask}"})
		return web.json_response(if_info,status=200)
