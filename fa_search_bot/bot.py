from threading import Thread

import time

from telegram.ext import Updater
import logging
from telegram.utils.request import Request
import json

from fa_search_bot._version import __VERSION__
from fa_search_bot.fa_export_api import FAExportAPI
from fa_search_bot.functionalities.beep import BeepFunctionality
from fa_search_bot.functionalities.image_hash_recommend import ImageHashRecommendFunctionality
from fa_search_bot.functionalities.inline import InlineFunctionality
from fa_search_bot.functionalities.menus import MenuFunctionality, MenuCallbackFunctionality
from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.functionalities.subscriptions import SubscriptionFunctionality, BlocklistFunctionality, \
    ChannelSubscriptionFunctionality, ChannelBlocklistFunctionality
from fa_search_bot.functionalities.supergroup_upgrade import SupergroupUpgradeFunctionality
from fa_search_bot.functionalities.unhandled import UnhandledMessageFunctionality
from fa_search_bot.functionalities.welcome import WelcomeFunctionality
from fa_search_bot.mqbot import MQBot
from fa_search_bot.subscription_watcher import SubscriptionWatcher

logger = logging.getLogger("fa_search_bot")


class FASearchBot:

    VERSION = __VERSION__

    def __init__(self, conf_file):
        with open(conf_file, 'r') as f:
            self.config = json.load(f)
        self.bot_key = self.config["bot_key"]
        self.api_url = self.config['api_url']
        self.api = FAExportAPI(self.config['api_url'])
        self.bot = None
        self.alive = False
        self.functionalities = []
        self.subscription_watcher = None
        self.subscription_watcher_thread = None

    def start(self):
        request = Request(con_pool_size=8)
        self.bot = MQBot(token=self.bot_key, request=request)
        self.subscription_watcher = SubscriptionWatcher.load_from_json(self.api, self.bot)
        self.subscription_watcher_thread = Thread(target=self.subscription_watcher.run)
        updater = Updater(bot=self.bot, use_context=True)
        dispatcher = updater.dispatcher
        # logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

        self.functionalities = self.initialise_functionalities()
        for func in self.functionalities:
            logger.info("Registering functionality: %s", func.__class__.__name__)
            func.register(dispatcher)

        updater.start_polling()
        self.alive = True

        # Start the sub watcher
        self.subscription_watcher_thread.start()

        while self.alive:
            logger.info("Main thread alive")
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                self.alive = False
        logger.info("Shutting down")

        # Kill the sub watcher
        self.subscription_watcher.running = False
        self.subscription_watcher_thread.join()

    def initialise_functionalities(self):
        return [
            BeepFunctionality(),
            WelcomeFunctionality(),
            ImageHashRecommendFunctionality(),
            NeatenFunctionality(self.api),
            InlineFunctionality(self.api),
            SubscriptionFunctionality(self.subscription_watcher),
            ChannelSubscriptionFunctionality(self.subscription_watcher),
            BlocklistFunctionality(self.subscription_watcher),
            ChannelBlocklistFunctionality(self.subscription_watcher),
            SupergroupUpgradeFunctionality(self.subscription_watcher),
            MenuFunctionality(),
            MenuCallbackFunctionality(self.subscription_watcher),
            UnhandledMessageFunctionality(),
        ]
