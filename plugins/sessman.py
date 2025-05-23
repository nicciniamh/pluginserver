"""
Session Manager that uses either mongodb or sqlite3 for the backend.
"""
import os
import sqlite3
import uuid
import json
import time
import base64
import asyncio
from pymongo import MongoClient
from bson import ObjectId
from plugincore.baseplugin import BasePlugin
from aiohttp import web
from datetime import datetime, timedelta # Add timedelta
import pytz

electrolux_run_flag = True

def sqlite3_create_sql(table):
    """
    simple to build SQL to create the Sqlite3 table
    """
    create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            timestamp INTEGER NOT NULL,
            session_id TEXT NOT NULL UNIQUE,
            client_ip TEXT NOT NULL,
            data TEXT NOT NULL
        );
    """
    return create_sql

def is_connection_closed(conn):
    try:
        conn.execute("SELECT 1")
        return False
    except sqlite3.ProgrammingError:
        return True
    except sqlite3.Error as e:
         print(f"An unexpected SQLite error occurred: {e}")
         return True

async def electrolux(**kwargs):
    """
    This is the sqlite session database vacuum thread
    """
    global electrolux_run_flag
    log = kwargs.get('log')
    required_args = ['database', 'table', 'sem', 'interval', 'ttl']
    for k in required_args:
        if not kwargs.get(k):
            raise AttributeError(f"Required argument missing or invalid: {k}")
    database = kwargs.get('database')
    table = kwargs.get('table')
    sem = kwargs.get('sem')
    interval = kwargs.get('interval')
    ttl = kwargs.get('ttl')
    con = None
    error_attempts = 0
    max_errors = 50
    loop_start_time = time.time() - interval
    try:
        while electrolux_run_flag:
            current_time = time.time()
            if (time.time() - loop_start_time) > interval:
                loop_start_time = time.time()
                if not con or is_connection_closed(con):
                    try:
                        if os.path.exists(database):
                            con = sqlite3.connect(database)
                    except Exception as e:
                        log.exception(f"electrolux: Could not establish a connection on database {database}: {e}")
                        error_attempts = error_attempts + 1
                        if (error_attempts > max_errors):
                            raise
                try:
                    async with sem:
                        aged = int(time.time()) - ttl
                        cur = con.cursor()
                        cur.execute(f"""
                            DELETE FROM {table} WHERE timestamp < ?;
                        """, (aged,))
                        con.commit()  # Ensure changes are written
                        cur.close()
                        error_attempts = 0
                except sqlite3.Error as e:
                    log.exception(f"SQLite error in electrolux thread: {e}")
                    if con:
                        con.rollback()  # Rollback any pending changes
                        con.close()
                        error_attempts = error_attempts + 1
                        if (error_attempts > max_errors):
                            raise
                except Exception as e:
                    log.exception(f"An unexpected error occurred in electrolux thread: {e}")
                    error_attempts = error_attempts + 1
                    if (error_attempts > max_errors):
                        raise
            await asyncio.sleep(1)
    finally:
        if con:
            con.close()

db_semaphore = asyncio.Lock()
db_vacuum = None

class SessionDatabase:
    """ Base class for session database handlers """
    def __init__(self,**kwargs):
        self.collection = kwargs.get('collection','sessions')   # collection or table`
        self.database = kwargs.get('database')                  # database to use or file
        self.username  = kwargs.get('username')                 # database username
        self.password = kwargs.get('password')                  # password for db (mongodb)
        self.server_url = kwargs.get('server_url')              # server url for mongodb
        self.session_ttl = kwargs.get('session_ttl',86400)      # session ttl
        self.sem = db_semaphore
        self.data = kwargs.get('data',{})
        self.kwargs = kwargs

    def _encode_data(self,data):
        jdata = json.dumps(data).encode('utf-8')
        bdata = base64.b64encode(jdata).decode('utf-8')
        return bdata

    def _decode_data(self,bdata):
        bdata = bdata.encode('utf-8')
        jdata = base64.b64decode(bdata).decode('utf-8')
        return json.loads(jdata)

class SessionSqlite(SessionDatabase):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.db_con = None
        self.log = kwargs.get('log')
        if not getattr(self,'database'):
            raise ValueError('No database specified')

    @staticmethod
    async def new(**kwargs):
        global electrolux_run_flag
        """
        set up a new instance of SessionSqlite along with initializing
        the vacuum task to sweep away old sessions
        """
        global db_vacuum
        inst = SessionSqlite(**kwargs)
        async with inst.sem:
            con = sqlite3.connect(inst.database)
            cur = con.cursor()
            cur.execute(sqlite3_create_sql(inst.collection));
            cur.close()

        """
        This is where we set up the vacuum with electrolux. It's intentionally
        set up to be completely independent other than the Lock it uses. 
        """
        vargs = {
            'database': inst.database,
            'table': inst.collection,
            'sem': inst.sem, 
            'ttl': inst.session_ttl,
            'interval': kwargs.get('vacuum_interval',60),
            'log': inst.log,
        }
        if  not db_vacuum:  # onlt set up one vacuum
            electrolux_run_flag = True
            try:
                db_vacuum = asyncio.create_task(electrolux(**vargs),name="vacuum_thread:electrolux")
            except Exception as e:
                inst.log.exception(f"{type(e)}: Error starting vacuum thread, {e}")
            await asyncio.sleep(.2)
            if db_vacuum.done():
                e = db_vacuum.exception()
                if e:
                    raise e
                inst.log.info(f"Created vacuum task {db_vacuum.get_name()}")

        return inst

    def connect_db(self):
        if not self.db_con or is_connection_closed(self.db_con):
            try:
                self.db_con = sqlite3.connect(self.database)
            except Exception as e:
                self.log.exception(f"connect_db: {type(e)}: Cannot open  sqlite3 database {self.database}: {e}")
                raise
        return self.db_con 

    async def _get_session_record(self, session_id,client_ip):
        con = self.connect_db()
        cur = con.cursor()
        cur.row_factory = sqlite3.Row
        session = None
        timestamp = int(time.time())
        try:
            async with db_semaphore:
                cur.execute(f"SELECT * from {self.collection} where session_id=? and client_ip=?",(session_id,client_ip))
                r = cur.fetchone()
                if r:
                    session={k: r[k] for k in r.keys()}
                    cur.execute(f"UPDATE {self.collection} set timestamp=? where session_id=? and client_ip=?",(timestamp,session_id,client_ip))
                    if not cur.rowcount:
                        self.log.error(f"Update {session_id} failed.")
                        session = None
                    else:
                        self.log.debug(f"get_session_record updated {cur.rowcount}")
                        con.commit()
        except Exception as  e:
            raise
        finally:
            return session

    async def create_session(self,**kwargs):
        data = kwargs.get('data',{})
        session_id = str(uuid.uuid4())
        client_ip = kwargs.get('client_ip','noip')
        time_in = int(time.time())
        if not client_ip:
            raise ValueError("required argument, client_ip, not set")

        bdata = self._encode_data(data)
        async with self.sem:
            con = self.connect_db()
            cur = con.cursor();
            cur.execute(f"INSERT INTO {self.collection} VALUES (?, ?, ?, ?)", (time_in, session_id, client_ip, bdata))
            if not cur.rowcount:
                self.log(f"Insert session id failed")
            else:                
                con.commit()
            cur.close()
        self.log(f"create_session - created session_id {session_id}")
        return session_id

    async def update_session(self,**kwargs):
        time_in = int(time.time())
        data = kwargs.get('data')
        client_ip = kwargs.get('client_ip','noip')
        session_id = kwargs.get('session_id')

        if not client_ip:
            raise ValueError("required argument, client_ip, not set")
        if not session_id:
            raise ValueError("required argument, session_id, not set")
        if not data:
            raise ValueError("required argument, data, not set")

        self.data = data
        async with self.sem:
            bdata = self._encode_data(data)
            con = self.connect_db()
            cur = con.cursor();
            cur.execute(f"UPDATE {self.collection} SET data=?, timestamp=? WHERE session_id=? and client_ip=?",(bdata,time_in, session_id, client_ip))
            con.commit()
            cur.close()
        return data

    async def get_session(self,**kwargs):
        time_in = int(time.time())
        session_id = kwargs.get('session_id')
        client_ip = kwargs.get('client_ip','noip')
        data = None
        if not client_ip:
            raise ValueError("required argument, client_ip, not set")
        if not session_id:
            raise ValueError("required argument, session_id, not set")

        session = await self._get_session_record(session_id,client_ip)
        if session:
            data = self._decode_data(session['data'])
        return data


class SessionMongoDB(SessionDatabase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k in ['database','username','password']:
            if not kwargs.get(k) and not getattr(self,k):
                raise ValueError(f"missing value for {k}")

        url = kwargs.get('server_url','localhost:27017')
        if not self.database:
            raise ValueError('database must be specified')
        self.server_url = f"mongodb://{self.username}:{self.password}@{url}/{self.database}?authSource={self.database}"
        self.client = MongoClient(self.server_url)
        self.db = self.client[self.database]  # Database name
        self.sessions = self.db[self.collection]  # Collection for sessions
        self.log = kwargs.get('log')
        # Create TTL Index on the 'createdAt' field
        # Set the expiration time to 30 minutes (1800 seconds)
        self.sessions.create_index([('createdAt', 1)], expireAfterSeconds=self.session_ttl)


    @staticmethod
    async def new(**kwargs):
        return SessionMongoDB(**kwargs)

    async def create_session(self, **kwargs):
        """Create a new session and insert into MongoDB, using ObjectId as sessionId."""
        client_ip = kwargs.get('client_ip','noip')
        data = kwargs.get('data',{})
        created_at = datetime.utcnow()
        session = {
            'client_ip': client_ip,
            'createdAt': created_at,
            'updatedAt': created_at,  # Can be updated later
            'data': data  # Store any session data (e.g., user preferences, tokens, etc.)
        }

        # Insert the session into the MongoDB collection
        async with self.sem:
            result = self.sessions.insert_one(session)
        session_id = str(result.inserted_id)  # Get the ObjectId and convert to string
        return session_id

    async def get_session(self, **kwargs):
        """Retrieve a session from MongoDB by session ID (ObjectId)."""
        client_ip = kwargs.get('client_ip','noip')
        session_id = kwargs.get('session_id')
        session = None
        async with self.sem:
            session = self.sessions.find_one({'_id': ObjectId(session_id), 'client_ip': client_ip})

        if session:
            return session.data
        return None

    async def update_session(self, **kwargs):
        """Update the session's 'data' field using ObjectId as sessionId."""
        client_ip = kwargs.get('client_ip','noip')
        session_id = kwargs.get('session_id')
        data = kwargs.get('data',{})
        async with self.sem:
            session = self.sessions.find_one({'_id': ObjectId(session_id), 'client_ip': client_ip})
            if not session:
                raise KeyError(f"Session ID {session_id} for {client_ip} not found.")
            session['updatedAt'] = datetime.utcnow()
            session['data'] = data
            update_result = self.sessions.update_one(
                {'_id': ObjectId(session_id), 'client_ip': client_ip},
                {"$set": {'updatedAt': session['updatedAt'], 'data': session['data']}}
            )
            if update_result.modified_count > 0:
                return data
            return None
        return None

async def SessionDbHandler(handler_type,**kwargs):
    handlers = {'sqlite': SessionSqlite, 'mongodb': SessionMongoDB}
    if  not handler_type in handlers:
        raise TypeError(f"There is no handler for {handler_type}")
    return await handlers[handler_type].new(**kwargs)

class Sessman(BasePlugin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        url = kwargs.get('server_url','localhost:27017')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.database = kwargs.get('database')
        self.backend = kwargs.get('backend','mongodb')
        self.session_ttl = kwargs.get('session_ttl',86400)
        self.collection = kwargs.get('collection','sessions')
        self.task_callback = kwargs.get('task_callback')
        self.kwargs = dict(kwargs)
        if  not hasattr(self,'log'):
            raise RuntimeError(f"{self._plugin_id}: No log instance from BasePlugin");
        if not self.database:
            raise ValueError('database must be specified')
        self.kwargs['log'] = self.log
        self.initialized = False

    async def initialize(self,**kwargs):
        if not self.initialized:
            self.db_handler = await SessionDbHandler(self.backend, **self.kwargs)
            self.initialized = True
            self.log.info(f"db backend initilized for {self.backend}")

    def terminate_plugin(self):
        global electrolux_run_flag
        electrolux_run_flag = False

    async def request_handler(self,**args):
#        if not self.initialized:
#            await self.initialize()
        session_id = args.get('session_id')
        if not session_id:
            if 'PS_SESSID' in args['request'].cookies:
                session_id = args['request'].cookies['PS_SESSID']
                args['session_id'] = session_id
        response_data= {'error': 'Invalid  reequest'}
        code = 400
        sessid = None
        if args['subpath'] == 'new':
            try:
                sessid = await self.db_handler.create_session(**args)
                if sessid:
                    code = 200
                    response_data = {'session_id': sessid}
            except Exception as e:
                code = 404
                response_data['error'] = f"Cannot get new session id {e}"
                response_data['locus'] = "sessman.new"

        elif args['subpath'] == 'update':
            if not session_id:
                code = 400
                response_data['error'] = 'no session id available'
                response_data['locus'] = "sessman.update"

            else:
                try:
                    data = await self.db_handler.update_session(**args)
                    if data:
                        code = 200
                        response_data = {'session_id': args['session_id'],'data': data}
                except KeyError as e:
                    response_data['error'] = f"{e}"
                except Exception as e:
                    code = 400
                    response_data['error'] = f"Cannot get update session  for session  id {e}"
                    response_data['locus'] = "sessman.update"


        elif args['subpath'] == 'get':
            if not session_id:
                code = 400
                response_data['error'] = 'no session id available'
            else:
                try:
                    data = await self.db_handler.get_session(**args)
                    if data:
                        code = 200
                        response_data = {'session_id': args.get('session_id'), 'data': data} # Convert ObjectId to string for response
                    else:
                        code = 404
                        response_data['error'] = f"Session ID {session_id} not found."
                        response_data['locus'] = "sessman.get"
                except Exception as e:
                    code = 400
                    response_data['error'] = f"Cannot get session for session id {session_id}: {e}"

        else:
            code = 400
            response_data = {'error': f"{args['subpath']} is not a valid endpoint"}

        response = web.json_response(response_data,status=code);
        if(sessid):
            now_utc = datetime.now(pytz.utc)
            expiry_time = now_utc + timedelta(seconds=self.session_ttl)
            response.set_cookie('PS_SESSID',sessid, expires=expiry_time, httponly=True)
        self.log.debug(f"{self._plugin_id}: response_handler {code}, {response_data}")
        return code, response
