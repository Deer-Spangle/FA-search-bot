import logging
from typing import Dict

import telegram
from telegram.ext import MessageQueue, messagequeue as mq

logger = logging.getLogger(__name__)


class MQBot(telegram.bot.Bot):
    """A subclass of Bot which delegates send method handling to MQ"""
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or MessageQueue()

    @mq.queuedmessage
    def _send_message(self, *args, **kwargs):
        logger.debug("Sending message")
        return super(MQBot, self).send_message(*args, **kwargs)

    def send_message(self, chat_id, *args, **kwargs):
        return self._send_message(chat_id, *args, **kwargs, isgroup=chat_id < 0)

    def _send_photo_roll_param(self, chat_id: int, photo: str, *args, **kwargs):
        logger.debug("Sending photo")
        try:
            return super(MQBot, self).send_photo(chat_id, photo, *args, **kwargs)
        except telegram.error.BadRequest:
            logger.info("Failed to send photo, rolling random param")
            param = 1
            while param < 5:
                try:
                    url = f"{photo}?rand={param}"
                    if "?" in photo:
                        url = f"{photo}&rand={param}"
                    return super(MQBot, self).send_photo(chat_id, url, *args, **kwargs)
                except telegram.error.BadRequest:
                    param += 1
            logger.warning("Failed to send photo at all, after trying params")

    @mq.queuedmessage
    def _send_photo(self, chat_id: int, photo: str, *args, **kwargs):
        self._send_photo_roll_param(chat_id, photo, *args, **kwargs)

    def send_photo(self, chat_id: int, photo: str, *args, **kwargs):
        return self._send_photo(chat_id, photo, *args, **kwargs, isgroup=chat_id < 0)

    @mq.queuedmessage
    def _send_photo_with_backup(self, chat_id: int, kwargs: Dict, kwargs_backup: Dict, isgroup: bool = None):
        logger.debug("Sending a photo with backup")
        try:
            photo = kwargs.pop("photo")
            return self._send_photo_roll_param(chat_id, photo, isgroup=isgroup, **kwargs)
        except telegram.error.BadRequest:
            logger.info("Sending photo by backup")
            photo = kwargs_backup.pop("photo")
            return self._send_photo_roll_param(chat_id, photo, isgroup=isgroup, **kwargs_backup)

    def send_photo_with_backup(self, chat_id: int, kwargs: Dict, kwargs_backup: Dict):
        return self._send_photo_with_backup(chat_id, kwargs, kwargs_backup, isgroup=chat_id < 0)

    @mq.queuedmessage
    def _send_document(self, *args, **kwargs):
        logger.debug("Sending document")
        return super(MQBot, self).send_document(*args, **kwargs)

    def send_document(self, chat_id, *args, **kwargs):
        return self._send_document(chat_id, *args, **kwargs, isgroup=chat_id < 0)

    @mq.queuedmessage
    def _send_audio(self, *args, **kwargs):
        logger.debug("Sending audio")
        return super(MQBot, self).send_audio(*args, **kwargs)

    def send_audio(self, chat_id, *args, **kwargs):
        return self._send_audio(chat_id, *args, **kwargs, isgroup=chat_id < 0)

    def stop(self):
        self._msg_queue.stop()
