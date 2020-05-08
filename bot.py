from threading import Thread

import telegram
import time

from telegram.ext import Updater, MessageQueue
from telegram.ext import messagequeue as mq
import logging
from telegram.utils.request import Request
import json

from _version import __VERSION__
from fa_export_api import FAExportAPI
from functionalities.beep import BeepFunctionality
from functionalities.image_hash_recommend import ImageHashRecommendFunctionality
from functionalities.inline import InlineFunctionality
from functionalities.neaten import NeatenFunctionality
from functionalities.subscriptions import SubscriptionFunctionality, BlacklistFunctionality
from functionalities.unhandled import UnhandledMessageFunctionality
from functionalities.welcome import WelcomeFunctionality
from subscription_watcher import SubscriptionWatcher


class MQBot(telegram.bot.Bot):
    """A subclass of Bot which delegates send method handling to MQ"""
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or MessageQueue()

    @mq.queuedmessage
    def _send_message(self, *args, **kwargs):
        return super(MQBot, self).send_message(*args, **kwargs)

    def send_message(self, chat_id, *args, **kwargs):
        return self._send_message(chat_id, *args, **kwargs, isgroup=chat_id < 0)

    @mq.queuedmessage
    def _send_photo(self, *args, **kwargs):
        return super(MQBot, self).send_photo(*args, **kwargs)

    def send_photo(self, chat_id, *args, **kwargs):
        return self._send_photo(chat_id, *args, **kwargs, isgroup=chat_id < 0)

    @mq.queuedmessage
    def _send_document(self, *args, **kwargs):
        return super(MQBot, self).send_document(*args, **kwargs)

    def send_document(self, chat_id, *args, **kwargs):
        return self._send_document(chat_id, *args, **kwargs, isgroup=chat_id < 0)

    @mq.queuedmessage
    def _send_audio(self, *args, **kwargs):
        return super(MQBot, self).send_audio(*args, **kwargs)

    def send_audio(self, chat_id, *args, **kwargs):
        return self._send_audio(chat_id, *args, **kwargs, isgroup=chat_id < 0)


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
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

        self.functionalities = self.initialise_functionalities()
        for func in self.functionalities:
            func.register(dispatcher)

        updater.start_polling()
        self.alive = True

        # Start the sub watcher
        self.subscription_watcher_thread.start()

        while self.alive:
            print("Main thread alive")
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                self.alive = False

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
            BlacklistFunctionality(self.subscription_watcher),
            UnhandledMessageFunctionality()
        ]
