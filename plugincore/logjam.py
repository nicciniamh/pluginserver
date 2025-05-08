import logging
import time
import io

class LogJam:
    def __init__(self, **kwargs):
        self.log_level = kwargs.get('level', logging.DEBUG)
        self.log_name = kwargs.get('name', 'NONAME')
        self.log_file = kwargs.get('file', None)

        # Convert string log level to logging constant if needed
        if isinstance(self.log_level, str):
            self.log_level = getattr(logging, self.log_level.upper(), logging.DEBUG)

        self.logger = logging.getLogger(self.log_name)
        self.logger.setLevel(self.log_level)

        # Prevent duplicate handlers if logger already exists
        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            # Console (stdout) handler
            ch = logging.StreamHandler()
            ch.setLevel(self.log_level)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

            # Optional file handler
            if self.log_file:
                fh = logging.FileHandler(self.log_file)
                fh.setLevel(self.log_level)
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)

    def __call__(self,*args):
        self.info(*args)

    def common_log(self,**kwargs):
        #ip, user_ident, user_auth, timestamp, method, path, protocol, status, size,file=None):
        user_ident = kwargs.get('user_ident','-')
        user_auth = kwargs.get('user_auth','-')
        timestamp = kwargs.get('timestamp',time.time())
        bad_keys = []
        for k in ['ip','method','protocol','path','status','size']:
            kv = kwargs.get(k) or None
            if not kv:
                bad_keys.append(k)
        if len(bad_keys):
            raise AttributeError(f"No value(s) given for {' '.join(bad_keys)}")
        ip = kwargs.get('ip')
        method = kwargs.get('method')
        path = kwargs.get('path')
        protocol = kwargs.get('protocol')
        status  = kwargs.get('status')
        size = kwargs.get('size')
        file = kwargs.get('file')
        time_str = time.strftime("%d/%b/%Y:%H:%M:%S %z",time.localtime(timestamp))
        lstr = f'{ip} {user_ident} {user_auth} [{time_str}] "{method} {path} {protocol}" {status} {size}'
        if type(file) is str:
            with open(file,'a') as f:
                print(lstr,file=f)
        elif isinstance(file,io.IOBase):
            print(lstr,file=file)
        return lstr
    
    def debug(self, *args):     self.logger.debug(*args)
    def info(self, *args):      self.logger.info(*args)
    def warning(self, *args):   self.logger.warning(*args)
    def error(self, *args):     self.logger.error(*args)
    def critical(self, *args):  self.logger.critical(*args)
    def exception(self, *args): self.logger.exception(*args)
