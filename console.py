#!/usr/bin/env python

import signal
from asyncio import get_event_loop, sleep
from interface import Interface
from PJON_daemon_client import listen, send, proto


def parse_user_input(user_input):
    user_input = user_input.split()
    dest = int(user_input[0], base=0)
    msg = ' '.join(user_input[1:])
    return dest, msg


async def listen_pjon():
    async for p in listen():
        if isinstance(p, proto.PacketIngoingMessage):
            msg = p.data.decode('ascii')
            interface.new_line(f'0x{p.src:02x} > \'{msg}\'', 'blue')


async def send_message(line, dest, msg):
    result = await send(dest, (msg).encode('ascii'))
    if result is proto.OutgoingResult.SUCCESS:
        line.color = 'green'
        line.content = line.content[:-len(' ...')]
    else:
        line.color = 'red'
        line.content = line.content[:-len(' ...')] + ' -> ' + result.name


async def main(interface):
    loop = get_event_loop()
    loop.create_task(listen_pjon())
    async for user_input in interface.get():
        try:
            dest, msg = parse_user_input(user_input)
            line = interface.new_line(f'0x{dest:02x} < \'{msg}\' ...',
                                      'bright_black')
            loop.create_task(send_message(line, dest, msg))
        except Exception:
            loop.create_task(interface.new_error('INVALID ENTRY'))


if __name__ == '__main__':
    interface = Interface()
    loop = get_event_loop()
    signal.signal(signal.SIGWINCH, lambda sig, action: interface.redraw())
    loop.run_until_complete(main(interface))
