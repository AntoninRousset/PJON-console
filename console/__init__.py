#!/usr/bin/env python

from .interface import Interface
from asyncio import get_event_loop, wait, Event, ensure_future

class ConsoleBase:

    def __init__(self, title):
        self.interface = Interface(title=title)

    async def run(self):
        fs = {
                self.interface.run(),
                self.run_extra()
                }
        await self.run_concurrent(fs)

    async def run_extra(self):
        from asyncio import sleep
        while True:
            await sleep(10)

    async def run_concurrent(self, fs):
        from concurrent.futures import FIRST_COMPLETED
        (done,),pending = await wait(fs, return_when=FIRST_COMPLETED)
        e = done.exception()
        try:
            for p in pending:
                p.cancel()
        except BaseException as e:
            self.logger.warning(f'Failed to cancel pending tasks: {e}')
        if e:
            raise e

