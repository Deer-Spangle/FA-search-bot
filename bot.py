import re

import requests
import telegram
import time

from telegram import Chat
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler
import logging
from telegram.utils.request import Request
import json


class FilterRegex(Filters.regex):

    def filter(self, message):
        text = message.text_markdown_urled or message.caption_markdown_urled
        if text:
            return bool(self.pattern.search(text))
        return False


class FASearchBot:
    FA_SUB_LINK = re.compile(r"furaffinity\.net/view/([0-9]+)", re.I)
    FA_DIRECT_LINK = re.compile(r"d\.facdn\.net/art/([^/]+)/(?:|stories/|poetry/|music/)([0-9]+)/", re.I)
    FA_LINKS = re.compile("{}|{}".format(FA_SUB_LINK.pattern, FA_DIRECT_LINK.pattern))

    def __init__(self, conf_file):
        with open(conf_file, 'r') as f:
            self.config = json.load(f)
        self.bot_key = self.config["bot_key"]
        self.api_url = self.config['api_url']
        self.bot = None
        self.alive = False

    def start(self):
        request = Request(con_pool_size=8)
        self.bot = telegram.Bot(token=self.bot_key, request=request)
        updater = Updater(bot=self.bot)
        dispatcher = updater.dispatcher
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

        beep_handler = CommandHandler('beep', self.beep)
        dispatcher.add_handler(beep_handler)

        start_handler = CommandHandler('start', self.welcome_message)
        dispatcher.add_handler(start_handler)

        neaten_handler = MessageHandler(FilterRegex(self.FA_LINKS), self.neaten_image)
        dispatcher.add_handler(neaten_handler)

        updater.start_polling()
        self.alive = True

        while self.alive:
            print("Main thread alive")
            time.sleep(30)

    def welcome_message(self, bot, update):
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Hello, I'm a new bot so I'm still learning. I can't do a whole lot yet. "
                 "If you have any suggestions, requests, or questions, direct them to @deerspangle.\n"
                 "For now, all I can do is neaten up any FA links you send me."
        )

    def beep(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="boop")

    def neaten_image(self, bot, update):
        message = update.message.text_markdown_urled or update.message.caption_markdown_urled
        submission_ids = []
        for match in self.FA_LINKS.finditer(message):
            submission_id = self._get_submission_id_from_link(bot, update, match.group(0))
            if submission_id:
                submission_ids.append(submission_id)
        # Remove duplicates, preserving order
        submission_ids = list(dict.fromkeys(submission_ids))
        # Handle each submission
        for submission_id in submission_ids:
            self._handle_fa_submission_link(bot, update, submission_id)

    def _get_submission_id_from_link(self, bot, update, link):
        sub_match = self.FA_SUB_LINK.match(link)
        if sub_match:
            return int(sub_match.group(1))
        direct_match = self.FA_DIRECT_LINK.match(link)
        username = direct_match.group(1)
        image_id = int(direct_match.group(2))
        submission_id = self._find_submission(username, image_id)
        if not submission_id:
            self._return_error_in_privmsg(
                bot, update,
                "Could not locate the image by {} with image id {}.".format(username, image_id)
            )
        return submission_id

    def _handle_fa_submission_link(self, bot, update, submission_id):
        print("Found a link, ID:{}".format(submission_id))
        sub_resp = requests.get("{}/submission/{}.json".format(self.api_url, submission_id))
        # If API returns fine
        if sub_resp.status_code == 200:
            sub_data = sub_resp.json()
            self._send_neat_fa_response(bot, update, sub_data)
        else:
            self._return_error_in_privmsg(bot, update, "This doesn't seem to be a valid FA submission: "
                                                       "https://www.furaffinity.net/view/{}/".format(submission_id))

    def _send_neat_fa_response(self, bot, update, submission_data):
        ext = submission_data['download'].split(".")[-1].lower()
        document_extensions = ["gif", "doc", "docx", "rtf", "txt", "pdf", "odt", "mid", "wav", "mp3", "mpeg"]
        photo_extensions = ["jpg", "jpeg", "png"]
        error_extensions = ["swf"]
        # Handle gifs, stories, music
        if ext in document_extensions:
            bot.send_document(
                chat_id=update.message.chat_id,
                document=submission_data['download'],
                caption=submission_data['link'],
                reply_to_message_id=update.message.message_id
            )
            return
        # Handle photos
        if ext in photo_extensions:
            bot.send_photo(
                chat_id=update.message.chat_id,
                photo=submission_data['download'],
                caption=submission_data['link'],
                reply_to_message_id=update.message.message_id
            )
            return
        # Handle known error extensions
        if ext in error_extensions:
            self._return_error_in_privmsg(bot, update, "I'm sorry, I can't neaten \".{}\" files.".format(ext))
            return
        self._return_error_in_privmsg(
            bot, update, "I'm sorry, I don't understand that file extension ({}).".format(ext)
        )

    def _return_error_in_privmsg(self, bot, update, error_message):
        # Only send an error message in private message
        if update.message.chat.type == Chat.PRIVATE:
            bot.send_message(
                chat_id=update.message.chat_id,
                text=error_message,
                reply_to_message_id=update.message.message_id
            )

    def _find_submission(self, username, image_id):
        folders = ["gallery", "scraps"]
        for folder in folders:
            submission_id = self._find_submission_in_folder(username, image_id, folder)
            if submission_id:
                return submission_id
        return False

    def _find_submission_in_folder(self, username, image_id, folder):
        page_listing = self._find_correct_page(username, image_id, folder)
        if not page_listing:
            # No page is valid.
            return False
        return self._find_submission_on_page(image_id, page_listing)

    def _find_submission_on_page(self, image_id, page_listing):
        for submission_data in page_listing:
            test_image_id = self._get_image_id_from_submission(submission_data)
            if image_id == test_image_id:
                return submission_data['id']
            if test_image_id < image_id:
                return False
        return False

    def _find_correct_page(self, username, image_id, folder):
        page = 1
        while True:
            listing = requests.get(
                "{}/user/{}/{}.json?page={}&full=1".format(self.api_url, username, folder, page)
            ).json()
            if len(listing) == 0:
                return False
            last_submission_data = listing[-1]
            if self._get_image_id_from_submission(last_submission_data) < image_id:
                return listing
            page += 1

    def _get_image_id_from_submission(self, submission_data):
        image_id = re.split(r"[-.]", submission_data['thumbnail'])[-2]
        return int(image_id)
