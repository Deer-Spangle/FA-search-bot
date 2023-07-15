from __future__ import annotations

import asyncio
import datetime
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fa_search_bot.subscriptions.subscription_watcher import SubscriptionWatcher


class Runnable(ABC):
    QUEUE_BACKOFF = 0.5

    def __init__(self, watcher: "SubscriptionWatcher"):
        self.watcher = watcher
        self.running = False

    @abstractmethod
    async def run(self) -> None:
        pass

    def stop(self) -> None:
        self.running = False

    async def _wait_while_running(self, seconds: float) -> None:
        sleep_end = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        while datetime.datetime.now() < sleep_end:
            if not self.running:
                break
            await asyncio.sleep(0.1)
