#!/usr/bin/env python3.6

from blessed import Terminal

def echo(*args):
    print(*args, end='', flush=True)
    

class Widget:

    def __init__(self, term, pos=(0,0), size=(0,0)):
        self.term = term
        self.pos = pos
        self.size = size

    def draw(self):
        raise NotImplementedError()

    def key_input(self, k):
        pass

    def focus(self):
        raise NotImplementedError()

    @property
    def pos(self):
        x,y = self._pos
        w,h = self.size
        if type(x) is float:
            x = int(x * self.term.width - w/2)
        else:
            x = self.term.width + x - w if x <= 0 else x
        if type(y) is float:
            y = int(y * self.term.height - h/2)
        else:
            y = self.term.height + y - h if y <= 0 else y
        return x,y

    @pos.setter
    def pos(self, pos):
        if type(pos) is not tuple or (type(pos) is tuple and len(pos) != 2):
            raise ValueError('Position has to be either of the form (x,y)')
        x,y = pos 
        if type(x) not in (int, float) or type(y) not in (int, float):
            raise ValueError('Position x and y has to be float or int not '
                    f'({type(x), type(y)})')
        self._pos = pos 

    @property
    def size(self):
        w,h = self._size
        if type(w) is float:
            w = int(w * self.term.width)
        else:
            w = self.term.width + w if w <= 0 else w
        if type(h) is float:
            h = int(h * self.term.height)
        else:
            h = self.term.height + h if h <= 0 else h
        return w,h

    @size.setter
    def size(self, size):
        if type(size) is not tuple or (type(size) is tuple and len(size) != 2):
            raise ValueError('Size has to be either of the form (w,h)')
        w,h = size
        if type(w) not in (int, float) or type(h) not in (int, float):
            raise ValueError('Size w and h has to be float or int not '
                    f'({type(w), type(h)})')
        self._size = size


class ConsoleScreen(Widget):

    def __init__(self, term, in_handler, title=None):
        super().__init__(term)
        self.frame = Frame(term, title=title, hlines={0,-3, -1})
        self.input_box = InputBox(term, pos=(2,-1), size=(-4, 1),
                in_handler=in_handler)
        self.log = Text(term, pos=(2,1), size=(-4,-5))

    def set_log(self, log):
        self.log.content = log

    def draw(self):
        self.frame.draw()
        self.input_box.draw()
        self.log.draw()

    def key_input(self, k):
        self.input_box.key_input(k)

    def focus(self):
        self.input_box.focus()


class ErrorScreen(Widget):

    def __init__(self, term, title=None, initial_msg=''):
        super().__init__(term)
        self.frame = Frame(term, title=title)
        self.text = Text(term, pos=(0.5,0.5), size=(0.5,0.5),
                text=initial_msg, halign='center', valign='middle')

    def draw(self):
        self.frame.draw()
        self.text.draw()

    def focus(self):
        self.term.hidden_cursor()


class Text(Widget):

    def __init__(self, term, pos, size, text='', halign='left', valign='top'):
        super().__init__(term, pos=pos, size=size)
        self.content = text
        self.halign = halign
        self.valign = valign

    def draw(self):
        w,h = self.size
        x0,y0 = self.pos
        lines = [s.strip() for s in self.content.split('\n')]
        nl = len(lines)
        c = {'left': '<', 'center': '^', 'right': '>'}[self.halign]
        y0 = {'top': 0, 'middle': int(h/2 - nl/2), 'bottom': int(h - nl)}[self.valign] + y0
        for i,l in enumerate(lines[-h:]):
            with self.term.location(x0, y0+i):
                echo(('{:' + c + str(w) + '}').format(l))


class Frame(Widget):

    def __init__(self, term, pos=(0,0), size=(0,0), title=None,
            hlines={0,-1}, vlines={0,-1}):
        super().__init__(term, pos=pos, size=size)
        self.title = title
        self.hlines = hlines
        self.vlines = vlines

    def draw(self):
        w,h = self.size
        for y in self.hlines:
            y = h+y if y < 0 else y
            self.draw_hline(y)
        for x in self.vlines:
            x = w+x if x < 0 else x
            self.draw_vline(x)
            for y in self.hlines:
                y = h+y if y < 0 else y
                self.draw_cross(x, y)
        if self.title:
            self.draw_title()

    def draw_hline(self, y):
        self.check_inside(y=y)
        w,h = self.size
        x0,y0 = self.pos
        with self.term.location(x0, y0+y):
            echo('─' * w)

    def draw_vline(self, x):
        self.check_inside(x=x)
        w,h = self.size
        x0,y0 = self.pos
        for y in range(0, h):
            with self.term.location(x0+x, y0+y):
                echo('│')

    def draw_cross(self, x, y):
        self.check_inside(x=x, y=y)
        w,h = self.size
        x0,y0 = self.pos
        corners = {(0,0): '┌', (w-1, 0): '┐', (0, h-1): '└', (w-1, h-1): '┘'} 
        if (x,y) in corners:
            c = corners[(x,y)]
        elif x == 0:
            c = '├'
        elif x == w-1:
            c = '┤'
        elif y == 0:
            c = '┬'
        elif y == h-1:
            c = '┴'
        else:
            c = '┼'
        with self.term.location(x0+x, y0+y):
            echo(c)

    def draw_title(self):
        w,h = self.size
        x0,y0 = self.pos
        title = f' {self.title} '
        x = int(w/2 - len(title)/2)
        with self.term.location(x0+x, y0):
            echo(self.term.bold + title + self.term.normal)

    def check_inside(self, x=None, y=None):
        w,h = self.size
        if x is not None and (x < 0 or x > w-1):
            raise ValueError('X coordinate out of bound '
                    f'({x} outside [{0}, {w-1}])')

        if y is not None and (y < 0 or y > h-1):
            raise ValueError('Y coordinate out of bound '
                    f'({y} outside [{0}, {h-1}])')

class InputBox(Widget):

    def __init__(self, term, pos, size, content='', in_handler=lambda msg:None):
        super().__init__(term, pos=pos, size=size)
        self.content = content
        self.cursor = len(content)
        self.in_handler = in_handler

    def put(self, s):
        p = self.cursor
        self.content= self.content[0:p] + s + self.content[p:]
        self.cursor += len(s)

    def remove(self, n):
        p = self.cursor
        self.content = self.content[0:max(p-n, 0)] + self.content[p:]
        self.move(-n)

    def move(self, n):
        p = self.cursor
        self.cursor = min(max(p+n, 0), len(self.content))

    def draw(self):
        w,h = self.size
        x0,y0 = self.pos
        with self.term.location(x0, y0):
            echo(('{:' + str(w) + 's}').format(self.content))

    def send(self):
        self.in_handler(self.content)
        self.content = ''
        self.cursor = 0
        
    def key_input(self, k):
        w,h = self.size
        moves = {'KEY_LEFT': -1, 'KEY_RIGHT': 1, '\x01': -w, '\x05': w}
        if k == 'KEY_ENTER':
            self.send()
        elif k == 'KEY_DELETE':
            self.remove(1)
        elif k in moves:
            self.move(moves[k])
        elif len(k) == 1 and ord(k) >= ord(u' '):
            self.put(k)
        with self.term.hidden_cursor():
            self.draw()

    def focus(self):
        x0,y0 = self.pos
        p = self.cursor
        echo(self.term.move(y0, x0+p))

