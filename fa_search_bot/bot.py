import asyncio
import dataclasses

from typing import Dict, Optional

import logging
import json

from prometheus_client import start_http_server, Info, Gauge
from telethon import TelegramClient
from yippi import AsyncYippiClient

from fa_search_bot._version import __VERSION__
from fa_search_bot.functionalities.functionalities import usage_counter
from fa_search_bot.functionalities.inline_edit import InlineEditFunctionality, InlineEditButtonPress
from fa_search_bot.functionalities.inline_gallery import InlineGalleryFunctionality
from fa_search_bot.sites.e621_handler import E621Handler
from fa_search_bot.sites.fa_export_api import FAExportAPI
from fa_search_bot.functionalities.beep import BeepFunctionality
from fa_search_bot.functionalities.image_hash_recommend import ImageHashRecommendFunctionality
from fa_search_bot.functionalities.inline import InlineSearchFunctionality
from fa_search_bot.functionalities.inline_favs import InlineFavsFunctionality
from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.functionalities.inline_neaten import InlineNeatenFunctionality
from fa_search_bot.functionalities.subscriptions import SubscriptionFunctionality, BlocklistFunctionality
from fa_search_bot.functionalities.supergroup_upgrade import SupergroupUpgradeFunctionality
from fa_search_bot.functionalities.unhandled import UnhandledMessageFunctionality
from fa_search_bot.functionalities.welcome import WelcomeFunctionality
from fa_search_bot.sites.fa_handler import FAHandler
from fa_search_bot.sites.sendable import initialise_metrics_labels
from fa_search_bot.subscription_watcher import SubscriptionWatcher

logger = logging.getLogger(__name__)
info = Info("fasearchbot_info", "Information about the FASearchBot instance")
start_time = Gauge("fasearchbot_startup_unixtime", "Last time FASearchBot was started")


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
class E621Config:
    username: str
    api_key: str

    @classmethod
    def from_dict(cls, conf: Dict) -> 'E621Config':
        return cls(
            conf["username"],
            conf["api_key"]
        )


@dataclasses.dataclass
class Config:
    fa_api_url: str
    telegram: TelegramConfig
    e621: E621Config
    prometheus_port: Optional[int]

    @classmethod
    def from_dict(cls, conf: Dict) -> 'Config':
        return cls(
            conf["api_url"],
            TelegramConfig.from_dict(conf),
            E621Config.from_dict(conf["e621"]),
            conf.get("prometheus_port", 7065)
        )


class FASearchBot:

    VERSION = __VERSION__

    def __init__(self, conf_file):
        with open(conf_file, 'r') as f:
            self.config = Config.from_dict(json.load(f))
        self.api = FAExportAPI(self.config.fa_api_url)
        self.e6_api = AsyncYippiClient("FA-search-bot", __VERSION__, self.config.e621.username)
        self.e6_handler = E621Handler(self.e6_api)
        self.client = None
        self.alive = False
        self.functionalities = []
        self.subscription_watcher = None
        self.subscription_watcher_thread = None
        self.log_task = None
        self.watcher_task = None

    @property
    def bot_key(self):
        return self.config.telegram.bot_token

    def start(self):
        start_http_server(self.config.prometheus_port)
        info.info({
            "version": __VERSION__,
        })
        start_time.set_to_current_time()
        self.e6_api.login(self.config.e621.username, self.config.e621.api_key)
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
        self.log_task = event_loop.create_task(self.periodic_log())
        # Start the sub watcher
        self.watcher_task = event_loop.create_task(self.subscription_watcher.run())

    def run(self):
        try:
            self.client.run_until_disconnected()
        finally:
            self.close()

    def close(self):
        # Shut down sub watcher
        self.alive = False
        self.subscription_watcher.running = False
        event_loop = asyncio.get_event_loop()
        if self.watcher_task is not None:
            event_loop.run_until_complete(self.watcher_task)
        if self.log_task is not None:
            event_loop.run_until_complete(self.log_task)
        if self.e6_api is not None:
            event_loop.run_until_complete(self.e6_api.close())

    async def periodic_log(self):
        while self.alive:
            logger.info("Main thread alive")
            try:
                await asyncio.sleep(20)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                self.alive = False
        logger.info("Shutting down")

    def initialise_functionalities(self):
        fa_handler = FAHandler(self.api)
        handlers = {
            fa_handler.site_code: fa_handler,
            self.e6_handler.site_code: self.e6_handler,
        }
        initialise_metrics_labels(list(handlers.values()))
        functionalities = [
            BeepFunctionality(),
            WelcomeFunctionality(),
            ImageHashRecommendFunctionality(),
            NeatenFunctionality(handlers),
            InlineFavsFunctionality(self.api),
            InlineGalleryFunctionality(self.api),
            InlineNeatenFunctionality(handlers),
            InlineSearchFunctionality(self.api),
            InlineEditFunctionality(handlers, self.client),
            InlineEditButtonPress(handlers),
            SubscriptionFunctionality(self.subscription_watcher),
            BlocklistFunctionality(self.subscription_watcher),
            SupergroupUpgradeFunctionality(self.subscription_watcher),
            UnhandledMessageFunctionality(),
        ]
        for functionality in functionalities:
            for label in functionality.usage_labels:
                usage_counter.labels(function=label)
        return functionalities
