from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
from math import ceil
from typing import TYPE_CHECKING

from prometheus_client import Gauge, Info, start_http_server  # type: ignore
from telethon import TelegramClient
from yippi import AsyncYippiClient

from fa_search_bot._version import __VERSION__
from fa_search_bot.database import Database
from fa_search_bot.functionalities.beep import BeepFunctionality
from fa_search_bot.functionalities.functionalities import usage_counter
from fa_search_bot.functionalities.image_hash_recommend import ImageHashRecommendFunctionality
from fa_search_bot.functionalities.inline_edit import InlineEditButtonPress, InlineEditFunctionality
from fa_search_bot.functionalities.inline_favs import InlineFavsFunctionality
from fa_search_bot.functionalities.inline_gallery import InlineGalleryFunctionality
from fa_search_bot.functionalities.inline_neaten import InlineNeatenFunctionality
from fa_search_bot.functionalities.inline_search import InlineSearchFunctionality
from fa_search_bot.functionalities.neaten import NeatenFunctionality, \
    NeatenDocumentFilenameFunctionality
from fa_search_bot.functionalities.subscriptions import BlocklistFunctionality, SubscriptionFunctionality
from fa_search_bot.functionalities.supergroup_upgrade import SupergroupUpgradeFunctionality
from fa_search_bot.functionalities.unhandled import UnhandledMessageFunctionality
from fa_search_bot.functionalities.welcome import WelcomeFunctionality
from fa_search_bot.sites.e621.e621_handler import E621Handler
from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
from fa_search_bot.sites.furaffinity.fa_handler import FAHandler
from fa_search_bot.sites.handler_group import HandlerGroup
from fa_search_bot.sites.sendable import initialise_metrics_labels
from fa_search_bot.sites.weasyl.weasyl_handler import WeasylHandler
from fa_search_bot.submission_cache import SubmissionCache
from fa_search_bot.subscriptions.subscription_watcher import SubscriptionWatcher

if TYPE_CHECKING:
    from asyncio import Task
    from typing import Optional

    from fa_search_bot.functionalities.functionalities import BotFunctionality


logger = logging.getLogger(__name__)
info = Info("fasearchbot_info", "Information about the FASearchBot instance")
start_time = Gauge("fasearchbot_startup_unixtime", "Last time FASearchBot was started")


@dataclasses.dataclass
class TelegramConfig:
    api_id: int
    api_hash: str
    bot_token: str

    @classmethod
    def from_dict(cls, conf: dict) -> "TelegramConfig":
        return cls(conf["telegram_api_id"], conf["telegram_api_hash"], conf["bot_key"])


@dataclasses.dataclass
class E621Config:
    username: str
    api_key: str

    @classmethod
    def from_dict(cls, conf: dict) -> "E621Config":
        return cls(conf["username"], conf["api_key"])


@dataclasses.dataclass
class WeasylConfig:
    api_key: str

    @classmethod
    def from_dict(cls, conf: dict) -> "WeasylConfig":
        return cls(conf["api_key"])


@dataclasses.dataclass
class SubscriptionWatcherConfig:
    enabled: bool
    num_data_fetchers: int
    num_media_uploaders: int

    @classmethod
    def from_dict(cls, conf: dict) -> "SubscriptionWatcherConfig":
        return cls(
            enabled=conf.get("enabled", True),
            num_data_fetchers=conf.get("num_data_fetchers", 2),
            num_media_uploaders=conf.get("num_media_uploaders", 2),
        )


@dataclasses.dataclass
class Config:
    fa_api_url: str
    telegram: TelegramConfig
    e621: E621Config
    weasyl: Optional[WeasylConfig]
    subscription_watcher: SubscriptionWatcherConfig
    prometheus_port: Optional[int]

    @classmethod
    def from_dict(cls, conf: dict) -> "Config":
        weasyl_data = conf.get("weasyl")
        weasyl_config = None
        if weasyl_data:
            weasyl_config = WeasylConfig.from_dict(weasyl_data)
        return cls(
            conf["api_url"],
            TelegramConfig.from_dict(conf),
            E621Config.from_dict(conf["e621"]),
            weasyl_config,
            SubscriptionWatcherConfig.from_dict(conf.get("subscription_watcher", {})),
            conf.get("prometheus_port", 7065),
        )

    @classmethod
    def load_from_file(cls, file_name: str) -> "Config":
        with open(file_name, "r") as f:
            return cls.from_dict(json.load(f))


class FASearchBot:
    VERSION = __VERSION__

    def __init__(self, config: Config) -> None:
        self.config = config
        self.api = FAExportAPI(self.config.fa_api_url)
        self._e6_api: Optional[AsyncYippiClient] = None
        self._e6_handler: Optional[E621Handler] = None
        self.client: TelegramClient = TelegramClient(
            "fasearchbot", self.config.telegram.api_id, self.config.telegram.api_hash
        )
        self.alive = False
        self.functionalities: list[BotFunctionality] = []
        self.db = Database()
        self.submission_cache = SubmissionCache(self.db)
        self.subscription_watcher: SubscriptionWatcher = SubscriptionWatcher.load_from_json(
            self.api, self.client, self.submission_cache
        )
        self.log_task: Optional[Task] = None
        self.watcher_task: Optional[Task] = None

    @property
    def bot_key(self) -> str:
        return self.config.telegram.bot_token

    @property
    def e6_api(self) -> AsyncYippiClient:
        if self._e6_api is None:
            self._e6_api = AsyncYippiClient("FA-search-bot", __VERSION__, self.config.e621.username)
            self._e6_api.login(self.config.e621.username, self.config.e621.api_key)
        return self._e6_api

    @property
    def e6_handler(self) -> E621Handler:
        if self._e6_handler is None:
            self._e6_handler = E621Handler(self.e6_api)
        return self._e6_handler

    async def run(self) -> None:
        start_http_server(self.config.prometheus_port)
        info.info(
            {
                "version": __VERSION__,
            }
        )
        start_time.set_to_current_time()
        self.client.start(bot_token=self.config.telegram.bot_token)

        self.functionalities = self.initialise_functionalities()
        for func in self.functionalities:
            logger.info("Registering functionality: %s", func.__class__.__name__)
            func.register(self.client)
        self.alive = True
        event_loop = asyncio.get_event_loop()

        # Log every couple seconds so we know the bot is still running
        self.log_task = event_loop.create_task(self.periodic_log())
        # Start the sub watcher
        if self.config.subscription_watcher.enabled:
            self.subscription_watcher.start_tasks()

        # Run the bot
        async with self.client:
            try:
                await self.client.run_until_disconnected()
            finally:
                self.close()

    def close(self) -> None:
        # Shut down sub watcher
        self.alive = False
        logger.debug("Shutting down subscription watcher")
        self.subscription_watcher.stop_tasks()
        event_loop = asyncio.get_event_loop()
        logger.debug("Shutting down periodic logger task")
        if self.log_task is not None:
            event_loop.run_until_complete(self.log_task)
        logger.debug("Shutting down e621 client")
        if self.e6_api is not None:
            event_loop.run_until_complete(self.e6_api.close())
        logger.debug("Shutting down FA client")
        if self.api is not None:
            event_loop.run_until_complete(self.api.close())
        logger.debug("Shutdown complete")

    async def periodic_log(self) -> None:
        sleep_seconds = 20
        sleep_increment = 0.1
        while self.alive:
            logger.info("Main thread alive")
            try:
                # Sleep with one eye open
                for _ in range(ceil(sleep_seconds/sleep_increment)):
                    await asyncio.sleep(sleep_increment)
                    if not self.alive:
                        break
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                self.alive = False
        logger.info("Shutting down")

    def initialise_functionalities(self) -> list[BotFunctionality]:
        fa_handler = FAHandler(self.api)
        handlers = [fa_handler, self.e6_handler]
        if self.config.weasyl:
            handlers.append(WeasylHandler(self.config.weasyl.api_key))
        handler_group = HandlerGroup(handlers, self.submission_cache)
        self.db.initialise_metrics(handler_group)
        initialise_metrics_labels(handler_group)
        self.submission_cache.initialise_metrics(handler_group)
        functionalities = [
            BeepFunctionality(),
            WelcomeFunctionality(),
            NeatenDocumentFilenameFunctionality(handler_group),
            ImageHashRecommendFunctionality(),
            NeatenFunctionality(handler_group),
            InlineFavsFunctionality(self.api, self.submission_cache),
            InlineGalleryFunctionality(self.api, self.submission_cache),
            InlineNeatenFunctionality(handler_group),
            InlineSearchFunctionality(handler_group, self.submission_cache),
            InlineEditFunctionality(handler_group, self.client),
            InlineEditButtonPress(handler_group),
            SubscriptionFunctionality(self.subscription_watcher),
            BlocklistFunctionality(self.subscription_watcher),
            SupergroupUpgradeFunctionality(self.subscription_watcher),
            UnhandledMessageFunctionality(),
        ]
        for functionality in functionalities:
            for label in functionality.usage_labels:
                usage_counter.labels(function=label)
        return functionalities
