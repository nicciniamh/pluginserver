import logging

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
        
    def debug(self, *args):     self.logger.debug(*args)
    def info(self, *args):      self.logger.info(*args)
    def warning(self, *args):   self.logger.warning(*args)
    def error(self, *args):     self.logger.error(*args)
    def critical(self, *args):  self.logger.critical(*args)
    def exception(self, *args): self.logger.exception(*args)
