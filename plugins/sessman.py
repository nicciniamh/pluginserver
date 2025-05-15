from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
from plugincore.baseplugin import BasePlugin

class Sessman(BasePlugin):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		url = kwargs.get('server_url','localhost:27017')
		self.username = kwargs.get('username')
		self.password = kwargs.get('password')
		self.database = kwargs.get('database')
		self.collection = kwargs.get('collection','sessions')
		if not self.database:
			raise ValueError('database must be specified')
		self.server_url = f"mongodb://{self.username}:{self.password}@{url}/{self.database}?authSource={self.database}"
		self.client = MongoClient(self.server_url)
		self.db = self.client[self.database]  # Database name
		self.sessions = self.db[self.collection]  # Collection for sessions

		# Create TTL Index on the 'createdAt' field
		# Set the expiration time to 30 minutes (1800 seconds)
		self.sessions.create_index([('createdAt', 1)], expireAfterSeconds=1800)

	def create_session(self, user_id, client_ip, data):
		"""Create a new session and insert into MongoDB, using ObjectId as sessionId."""
		created_at = datetime.utcnow()
		session = {
			'userId': user_id,
			'client_ip': client_ip,
			'createdAt': created_at,
			'updatedAt': created_at,  # Can be updated later
			'data': data  # Store any session data (e.g., user preferences, tokens, etc.)
		}

		# Insert the session into the MongoDB collection
		result = self.sessions.insert_one(session)
		session_id = str(result.inserted_id)  # Get the ObjectId and convert to string
		return result, session_id, session

	def get_session(self, session_id, client_ip):
		"""Retrieve a session from MongoDB by session ID (ObjectId)."""
		try:
			session = self.sessions.find_one({'_id': ObjectId(session_id), 'client_ip': client_ip})
			return session
		except Exception as e:
			self.log.debug(f"{self._plugin_id}: Invalid session_id format: {e}")
			return None

	def update_session(self, session_id, client_ip, data):
		"""Update the session's 'data' field using ObjectId as sessionId."""
		result = False
		try:
			session = self.sessions.find_one({'_id': ObjectId(session_id), 'client_ip': client_ip})
			if not session:
				raise KeyError(f"Session ID {session_id} for {client_ip} not found.")
			session['updatedAt'] = datetime.utcnow()
			session['data'] = data
			update_result = self.sessions.update_one(
				{'_id': ObjectId(session_id), 'client_ip': client_ip},
				{"$set": {'updatedAt': session['updatedAt'], 'data': session['data']}}
			)
			return update_result.modified_count > 0
		except Exception as e:
			self.log.debug(f"{self._plugin_id}: Error updating session with id {session_id}: {e}")
			return False

	def request_handler(self,**args):
		sessid = args.get('session_id')
		response_data= {'error': 'Invalid  reequest'}
		user = args.get('user','sessman')
		client_ip = args.get('client_ip','127.0.0.10')
		data=args.get('data',{})
		if args['subpath'] == 'new':
			client_ip = args.get('client_ip','127.0.0.10')
			try:
				result,sessid,session = self.create_session(user,client_ip,data)
				response_data = {'session_id': sessid, 'data': session['data']}
			except Exception as e:
				response_data['error'] = f"Cannot get new session id {e}"
		elif args['subpath'] == 'update':
			try:
				if self.update_session(sessid, client_ip, data):
					updated_session = self.get_session(sessid, client_ip)
					if updated_session:
						response_data = {'session_id': sessid, 'data': updated_session['data']}
					else:
						raise KeyError(f"Can't retrieve updated session for session id {sessid}")
				else:
					raise KeyError(f"Can't update session for session id {sessid}")
			except KeyError as e:
				response_data['error'] = f"{e}"
			except Exception as e:
				response_data['error'] = f"Cannot get update session  for session  id {e}"

		elif args['subpath'] == 'get':
			try:
				print(f"{self._plugin_id}: getting data for {sessid}:{client_ip}")
				session = self.get_session(sessid,client_ip)
				self.log.debug(f"Got session in {session}")
				if session:
					response_data = {'session_id': str(session['_id']), 'data': session['data']} # Convert ObjectId to string for response
				else:
					response_data['error'] = f"Session ID {sessid} not found."
			except Exception as e:
				response_data['error'] = f"Cannot get session for session id {sessid}: {e}"

		else:
			response_data = {'error': f"{args['subpath']} is not a valid endpoint"}

		if 'error' in response_data:
			code = 400
		else:
			code = 200
		self.log.debug(f"{self._plugin_id}: {code}, {response_data}")
		return code, response_data