#!/usr/bin/env python3.6

from blessed import Terminal
from asyncio import get_event_loop, sleep, Event
from concurrent.futures import ThreadPoolExecutor


def echo(*args):
    print(*args, end='', flush=True)


def use_color(term, c, t):
    return {
        'black':   term.black,
        'red':     term.red,
        'green':   term.green,
        'yellow':  term.yellow,
        'blue':    term.blue,
        'magenta': term.magenta,
        'cyan':    term.cyan,
        'white':   term.white,
        'bright_black':   term.bright_black,
        'bright_red':     term.bright_red,
        'bright_green':   term.bright_green,
        'bright_yellow':  term.bright_yellow,
        'bright_blue':    term.bright_blue,
        'bright_magenta': term.bright_magenta,
        'bright_cyan':    term.bright_cyan,
        'bright_white':   term.bright_white,
    }[c](t)


class Interface:

    def __init__(self):
        self.term = Terminal()
        self.frames = Frames(self.term)
        self.input_box = InputBox(self.term)
        self.text = Text(self.term)
        self.error_poster = Poster(self.term, -4, 0, color='red')

    async def get(self):
        with self.term.fullscreen(), self.term.cbreak():
            self.redraw()
            async for k in self.inkey():
                if k.name is 'KEY_ESCAPE':
                    return
                p = self.input_box.handle_inkey(k)
                if p is not None:
                    yield p

    def new_line(self, content=None, color='white'):
        return self.text.new_line(content, color)

    async def new_error(self, msg):
        await self.error_poster.display(msg)
        await self.error_poster.display('')
        self.redraw()

    async def inkey(self):
        loop = get_event_loop()
        executor = ThreadPoolExecutor()
        while True:
            yield await loop.run_in_executor(executor, self.term.inkey)

    def redraw(self):
        self.clear()
        self.frames.draw_frames('PJON console')
        self.text.redraw()
        self.error_poster.redraw()

    def clear(self):
        echo(self.term.clear())


class Frames:

    def __init__(self, term):
        self.term = term

    def draw_frames(self, title=None):
        with self.term.hidden_cursor():
            w, h = self.term.width, self.term.height

            for y in [0, h-3, h-1]:
                self.draw_hline(y)

            for x in [0, w-1]:
                self.draw_vline(x)

            for x, y, c in [(0,   0, '┌'), (w - 1, 0, '┐'),
                            (0, h-3, '├'), (w-1, h-3, '┤'),
                            (0, h-1, '└'), (w-1, h-1, '┘')]:
                with self.term.location(x, y):
                    echo(c)

            if title:
                self.draw_title(0, title)

    def draw_hline(self, y):
        with self.term.location(y=y):
            echo('─' * self.term.width)

    def draw_vline(self, x):
        for y in range(self.term.height):
            with self.term.location(x, y):
                echo('│')

    def draw_title(self, y, title):
        title = f' {title} '
        x = int(self.term.width/2 - len(title)/2)
        with self.term.location(x, y):
            echo(self.term.bold + title + self.term.normal)


class InputBox:

    def __init__(self, term, content=''):
        self.term = term
        self.cursor = len(content)
        self.content = content

    def handle_inkey(self, k):
        return {
            'KEY_LEFT': lambda k: self.move(-1),
            'KEY_RIGHT': lambda k: self.move(1),
            'KEY_ENTER': lambda k: self.send(),
            'KEY_DELETE': lambda k: self.remove(1)

            # TODO key end and home
            # TODO shift + arrows
            # csr.term.KEY_SLEFT: left_of(csr, 10),
            # csr.term.KEY_SRIGHT: right_of(csr, 10),
            # csr.term.KEY_SDOWN: below(csr, 10),
            # csr.term.KEY_SUP: above(csr, 10),

        }.get(k.name, lambda k: self.put(k))(str(k))

    def put(self, s):
        if len(s) != 1 or ord(s) < ord(u' ') or ord(s) > ord('~'):
            return
        p = self.cursor
        self.content = self.content[0:p] + s + self.content[p:]
        self.cursor += len(s)
        self.redraw()

    def remove(self, n):
        p = self.cursor
        self.content = self.content[0:max(p-n, 0)] + self.content[p:]
        self.move(-n)
        self.redraw()

    def move(self, n):
        p = self.cursor
        self.cursor = min(max(p+n, 0), len(self.content))
        self.redraw()

    def redraw(self):
        h = self.term.height
        with self.term.hidden_cursor(), self.term.location(1, h - 2):
            echo(' ' * (self.term.width - 2))
        with self.term.location(2, h - 2):
            echo(self.content[:(self.term.width - 4)])
        echo(self.term.move(self.term.height - 2, 2 + self.cursor))

    def send(self):
        content = self.content if len(self.content) > 0 else None
        self.content = ''
        self.cursor = 0
        self.redraw()
        return content


class Text:

    def __init__(self, term):
        self.term = term
        self.lines = []

    def new_line(self, content=None, color='white'):
        self.lines.append(Line(self, color=color))
        if content:
            self.lines[-1].content = content
        return self.lines[-1]

    def redraw(self):
        n = self.term.height - 4
        lines = self.lines[-n:]
        for i in range(n):
            with self.term.hidden_cursor(), self.term.location(1, i + 1):
                echo(' ' * (self.term.width - 2))
        for i, l in enumerate(lines):
            with self.term.hidden_cursor(), self.term.location(2, i + 1):
                echo(str(l)[:(self.term.width-4)])


class Line:

    def __init__(self, text, color='white'):
        self.text = text
        self.color = color
        self._content = ''

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, v):
        self._content = v
        self.text.redraw()

    def __str__(self):
        return str(use_color(self.text.term, self.color, self.content))


class Poster:

    def __init__(self, term, x, y, duration=2, content='', color='white'):
        self.term = term
        self.duration = duration
        self.x, self.y = x, y
        self.color = color
        self.content = content
        self.event = Event()
        self.event.set()

    async def display(self, msg):
        await self.event.wait()
        self.event.clear()
        self.content = msg
        self.redraw()
        await sleep(self.duration)
        self.event.set()

    def redraw(self):
        if not self.content or len(self.content.strip()) == 0:
            return
        with self.term.hidden_cursor(), self.term.location(*self.get_pos()):
            echo(use_color(self.term, self.color, f' {self.content} '))

    def get_pos(self):
        width = len(self.content) + 2
        x = self.x if self.x >= 0 else self.term.width + self.x - width
        y = self.y if self.y >= 0 else self.term.height + self.y
        return x, y

