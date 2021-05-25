import asyncio
import dataclasses

from typing import Dict

import logging
import json

from telethon import TelegramClient

from fa_search_bot._version import __VERSION__
from fa_search_bot.fa_export_api import FAExportAPI
from fa_search_bot.functionalities.beep import BeepFunctionality
from fa_search_bot.functionalities.image_hash_recommend import ImageHashRecommendFunctionality
from fa_search_bot.functionalities.inline import InlineFunctionality
from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.functionalities.subscriptions import SubscriptionFunctionality, BlocklistFunctionality
from fa_search_bot.functionalities.supergroup_upgrade import SupergroupUpgradeFunctionality
from fa_search_bot.functionalities.unhandled import UnhandledMessageFunctionality
from fa_search_bot.functionalities.welcome import WelcomeFunctionality
from fa_search_bot.subscription_watcher import SubscriptionWatcher

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class TelegramConfig:
    api_id: int
    api_hash: str
    bot_token: str

    @classmethod
    def from_dict(cls, conf: Dict) -> 'TelegramConfig':
        return cls(
            conf["telegram_api_id"],
            conf["telegram_api_hash"],
            conf["bot_key"]
        )


@dataclasses.dataclass
class Config:
    fa_api_url: str
    telegram: TelegramConfig

    @classmethod
    def from_dict(cls, conf: Dict) -> 'Config':
        return cls(
            conf["api_url"],
            TelegramConfig.from_dict(conf)
        )


class FASearchBot:

    VERSION = __VERSION__

    def __init__(self, conf_file):
        with open(conf_file, 'r') as f:
            self.config = Config.from_dict(json.load(f))
        self.api = FAExportAPI(self.config.fa_api_url)
        self.client = None
        self.alive = False
        self.functionalities = []
        self.subscription_watcher = None
        self.subscription_watcher_thread = None

    @property
    def bot_key(self):
        return self.config.telegram.bot_token

    def start(self):
        # request = Request(con_pool_size=8)
        self.client = TelegramClient("fasearchbot", self.config.telegram.api_id, self.config.telegram.api_hash)
        self.client.start(bot_token=self.config.telegram.bot_token)
        self.subscription_watcher = SubscriptionWatcher.load_from_json(self.api, self.client)

        self.functionalities = self.initialise_functionalities()
        for func in self.functionalities:
            logger.info("Registering functionality: %s", func.__class__.__name__)
            func.register(self.client)
        self.alive = True
        event_loop = asyncio.get_event_loop()

        # Log every couple seconds so we know the bot is still running
        log_task = event_loop.create_task(self.periodic_log())
        # Start the sub watcher
        watcher_task = event_loop.create_task(self.subscription_watcher.run())

        try:
            self.client.run_until_disconnected()
        finally:
            # Shut down sub watcher
            self.alive = False
            self.subscription_watcher.running = False
            event_loop.run_until_complete(watcher_task)
            event_loop.run_until_complete(log_task)

    async def periodic_log(self):
        while self.alive:
            logger.info("Main thread alive")
            try:
                await asyncio.sleep(2)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                self.alive = False
        logger.info("Shutting down")

    def initialise_functionalities(self):
        return [
            BeepFunctionality(),
            WelcomeFunctionality(),
            ImageHashRecommendFunctionality(),
            NeatenFunctionality(self.api),
            InlineFunctionality(self.api),
            SubscriptionFunctionality(self.subscription_watcher),
            BlocklistFunctionality(self.subscription_watcher),
            SupergroupUpgradeFunctionality(self.subscription_watcher),
            UnhandledMessageFunctionality(),
        ]
