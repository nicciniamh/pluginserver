import sys
import os
from datetime import datetime
# Standard Systemd/Syslog Priority Mapping

# "EMERG":   0,  # System is unusable
# "ALERT":   1,  # Action must be taken immediately
# "CRIT":    2,  # Critical conditions
# "ERR":     3,  # Error conditions
# "WARNING": 4,  # Warning conditions
# "NOTICE":  5,  # Normal but significant condition
# "INFO":    6,  # Informational
# "DEBUG":   7,  # Debug-level messages

LOG_PRIORITIES = {
    10:7,   # DEBUG
    20:6,   # INFO
    30:4,   # WARN
    40:3,   # ERROR
    50:2    # Exception
}

def os_print(output):
    output = f"{output}\n"
    try:
        os.write(1,output.encode('utf-8'))
    except BrokenPipeError:
        pass
class LogJam:
    def __init__(self, *, name=None, level="INFO",file=None, stdio=True):
        self.stdio = stdio
        if stdio and os.isatty(sys.stdout.fileno()):
            self.tty = True
        else:
            self.tty = False
        lc_config = {
            'level': level,
            'name': name, 
            'stdio': 'TRUE' if self.stdio else 'FALSE',
            'tty': self.tty,
            'logfile': file, 
        }
        #os_print(f"LOGGING CONFIG {lc_config}")

        self.file = file
        if self.file:
            self.logfile = open(self.file,'a')
        else:
            self.logfile = None
        if not name:
            raise ValueError("applicaiton mame must be specified in name")
        self.name = name
        self.levels = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40, "CRITICAL": 50, "EXCEPTION": 50}
        self.threshold = self.levels.get(level.upper(), 20)
        self.sysd_format = "<{priority}> - {level} - {name} - {msg}"
        self.std_format = "{timestamp} - {name} - {level} - {msg}"

        self.info(f"{self.name}: LogJam Config {lc_config}")

    def _output(self, level, *args):
        if self.levels[level] >= self.threshold:
            msgargs = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3],
                "priority": LOG_PRIORITIES[self.levels[level]],
                "name": self.name, 
                "level": level,
                "msg": ' '.join(map(str, args))
            }
            # if an output file was specified write there 
            if self.logfile:
                print(self.std_format.format(**msgargs),file=self.logfile)
                self.logfile.flush()
            # if we're not writing stdout to a tty assume a pipe to systemd
            if not self.tty:
                os_print(self.sysd_format.format(**msgargs))
            else:
                ## If stdout is a tty and stdio is true write to stdout 
                if self.stdio:
                    os_print(self.std_format.format(**msgargs))

    def __call__(self,*args):
        self._output("INFO",*args)

    def debug(self, *m): self._output("DEBUG", *m)
    def info(self, *m):  self._output("INFO", *m)
    def warn(self, *m):  self._output("WARN", *m)
    def error(self, *m): self._output("ERROR", *m)
    def critical(self, *m): self._output("CRITICAL", *m)
    def exception(self, *m): self._output("EXCEPTION", *m)
