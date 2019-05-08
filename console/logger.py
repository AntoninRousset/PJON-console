#!/usr/bin/env python

class Logger:

    def __init__(self, send_log):
        self.logs = []
        self.send_log = send_log

    def new(self, factory, *args, **kwargs):
        l = factory(self, *args, **kwargs)
        self.logs.append(l)
        self.update()
        return l

    def update(self):
        log = [m.format() for m in self.logs]
        self.send_log(log)


class Logmsg:

    def __init__(self, logger):
        from datetime import datetime 
        self.logger = logger
        self._time = datetime.now()

    def format(self):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()

    def time(self):
        h,m,s = self._time.hour, self._time.minute, self._time.second
        return f'{h:02d}:{m:02d}:{s:02d}'


class EmissionLogmsg(Logmsg):

    def __init__(self, logger, dest, msg):
        super().__init__(logger)
        self.dest = dest
        self.msg = msg
        self.status = 'PENDING'
        self.error = '???'

    def format(self):
        color = {
                'PENDING':  'bright_black',
                'ACK':      'green',
                'FAIL':     'red',
                }[self.status]
        return (color, str(self))

    def ack(self):
        self.status = 'ACK'
        self.logger.update()

    def fail(self, error):
        self.error = error
        self.status = 'FAIL'
        self.logger.update()

    def __str__(self):
        s = f'{self.time()} - 0x{self.dest:02x} < {self.msg}'
        if self.status == 'PENDING':
            s += ' ...'
        elif self.status == 'ACK':
            s += ' -> ACK'
        elif self.status == 'FAIL':
            s += f' -> FAIL: {self.error}'
        return s


class ReceptionLogmsg(Logmsg):

    def __init__(self, logger, src, msg):
        super().__init__(logger)
        self.src = src
        self.msg = msg

    def format(self):
        return ('cyan', str(self))

    def __str__(self):
        return f'{self.time()} - 0x{self.src:02x} > {self.msg}'


class ErrorLogmsg(Logmsg):

    def __init__(self, logger, error):
        super().__init__(logger)
        self.error = error

    def format(self):
        return ('red', str(self))

    def __str__(self):
        return f'{self.time()} - ERROR: {self.error}'


class WarningLogmsg(Logmsg):

    def __init__(self, logger, warning):
        super().__init__(logger)
        self.warning = warning

    def format(self):
        return ('yellow', str(self))

    def __str__(self):
        return f'{self.time()} - WARNING: {self.warning}'


