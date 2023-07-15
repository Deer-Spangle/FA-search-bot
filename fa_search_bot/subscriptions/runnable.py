from __future__ import annotations

import asyncio
import datetime
from abc import ABC, abstractmethod


class Runnable(ABC):
    def __init__(self):
        self.running = False

    @abstractmethod
    def run(self) -> None:
        pass

    def stop(self) -> None:
        self.running = False

    async def _wait_while_running(self, seconds: float) -> None:
        sleep_end = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        while datetime.datetime.now() < sleep_end:
            if not self.running:
                break
            await asyncio.sleep(0.1)
