#!/usr/bin/env python3.6

# dependencies:
#   - dev-python/blessed

from blessed import Terminal
from .widgets import ConsoleScreen, ErrorScreen 
from asyncio import get_event_loop, Queue, Event, sleep
from concurrent.futures import ThreadPoolExecutor, FIRST_COMPLETED
import os
import signal


class Interface:

    def __init__(self, title=None):
        self.q_in = Queue()
        self.q_out = Queue()
        self.term = Terminal()
        self._state = 'ERROR'
        self.screens = {
            'ERROR': ErrorScreen(self.term, title=title,
                initial_msg='Starting...'),
            'CONSOLE': ConsoleScreen(self.term, title=title,
                in_handler=lambda msg: self.q_in.put_nowait(msg)),
            }

    def draw_all(self):
        print(self.term.clear(), end='', flush=True)
        with self.term.hidden_cursor():
            self.screens[self.state].draw()
        self.focus()

    def set_log(self, log):
        colors = {
                'black':   self.term.black,  
                'red':     self.term.red,    
                'green':   self.term.green, 
                'yellow':  self.term.yellow, 
                'blue':    self.term.blue,   
                'magenta': self.term.magenta,
                'cyan':    self.term.cyan,   
                'white':   self.term.white,  
                'bright_black':   self.term.bright_black,  
                'bright_red':     self.term.bright_red,    
                'bright_green':   self.term.bright_green, 
                'bright_yellow':  self.term.bright_yellow, 
                'bright_blue':    self.term.bright_blue,   
                'bright_magenta': self.term.bright_magenta,
                'bright_cyan':    self.term.bright_cyan,   
                'bright_white':   self.term.bright_white,  
                }
        log = '\n'.join([colors[c](m) for c,m in log])
        self.screens['CONSOLE'].log.content = log
        if self.state == 'CONSOLE':
            with self.term.hidden_cursor():
                self.screens['CONSOLE'].log.draw()
        self.focus()

    def focus(self):
        self.screens[self.state].focus()

    def error(self, error):
        self.screens['ERROR'].text.content = error
        self.state = 'ERROR'

    def ok(self):
        self.state = 'CONSOLE'

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, s):
        self._state = s
        self.draw_all()

    async def run(self):
        signal.signal(signal.SIGWINCH, lambda s,a: self.draw_all())
        executor = ThreadPoolExecutor()
        while self.term.fullscreen():
            self.draw_all()
            while True:
                k = await self.get_key(executor)
                self.screens[self.state].key_input(k)
                self.focus()

    async def get(self):
        return await self.q_in.get()

    async def get_key(self, executor):
        loop = get_event_loop()
        with self.term.cbreak():
            while True:
                f = lambda: self.term.inkey(timeout=0.2)
                val = await loop.run_in_executor(executor, f)
                if val.is_sequence:
                    return val.name
                elif val:
                    return val

    async def key_input(self, k):
        await self.sreens[self.state].key_input(k)

