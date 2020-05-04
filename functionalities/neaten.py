import re
from typing import Optional, List

from telegram import Chat, Update
from telegram.ext import MessageHandler, CallbackContext

from filters import FilterRegex
from fa_export_api import PageNotFound
from fa_submission import FASubmissionFull, CantSendFileType, FASubmissionShort
from functionalities.functionalities import BotFunctionality, in_progress_msg


class NeatenFunctionality(BotFunctionality):
    FA_SUB_LINK = re.compile(r"furaffinity\.net/view/([0-9]+)", re.I)
    FA_DIRECT_LINK = re.compile(r"d\.facdn\.net/art/([^/]+)/(?:|stories/|poetry/|music/)([0-9]+)/", re.I)
    FA_THUMB_LINK = re.compile(r"t\.facdn\.net/([0-9]+)@[0-9]+-[0-9]+\.jpg")
    FA_LINKS = re.compile(f"{FA_SUB_LINK.pattern}|{FA_DIRECT_LINK.pattern}|{FA_THUMB_LINK.pattern}")

    def __init__(self, api):
        super().__init__(MessageHandler, filters=FilterRegex(self.FA_LINKS))
        self.api = api

    def call(self, update: Update, context: CallbackContext):
        with in_progress_msg(update, context, "Neatening image link"):
            message = update.message.text_markdown_urled or update.message.caption_markdown_urled
            submission_ids = []
            for match in self.FA_LINKS.finditer(message):
                submission_id = self._get_submission_id_from_link(context.bot, update, match.group(0))
                if submission_id:
                    submission_ids.append(submission_id)
            # Remove duplicates, preserving order
            submission_ids = list(dict.fromkeys(submission_ids))
            # Handle each submission
            for submission_id in submission_ids:
                self._handle_fa_submission_link(context.bot, update, submission_id)

    def _get_submission_id_from_link(self, bot, update, link: str) -> Optional[int]:
        # Handle submission page link matches
        sub_match = self.FA_SUB_LINK.match(link)
        if sub_match:
            return int(sub_match.group(1))
        # Handle thumbnail link matches
        thumb_match = self.FA_THUMB_LINK.match(link)
        if thumb_match:
            return int(thumb_match.group(1))
        # Handle direct file link matches
        direct_match = self.FA_DIRECT_LINK.match(link)
        username = direct_match.group(1)
        image_id = int(direct_match.group(2))
        submission_id = self._find_submission(username, image_id)
        if not submission_id:
            self._return_error_in_privmsg(
                bot, update,
                f"Could not locate the image by {username} with image id {image_id}."
            )
        return submission_id

    def _handle_fa_submission_link(self, bot, update, submission_id: int):
        print("Found a link, ID:{}".format(submission_id))
        try:
            submission = self.api.get_full_submission(str(submission_id))
            self._send_neat_fa_response(bot, update, submission)
        except PageNotFound:
            self._return_error_in_privmsg(bot, update, "This doesn't seem to be a valid FA submission: "
                                                       "https://www.furaffinity.net/view/{}/".format(submission_id))

    def _send_neat_fa_response(self, bot, update, submission: FASubmissionFull):
        try:
            submission.send_message(bot, update.message.chat_id, update.message.message_id)
        except CantSendFileType as e:
            self._return_error_in_privmsg(bot, update, str(e))

    def _return_error_in_privmsg(self, bot, update, error_message: str):
        # Only send an error message in private message
        if update.message.chat.type == Chat.PRIVATE:
            bot.send_message(
                chat_id=update.message.chat_id,
                text=error_message,
                reply_to_message_id=update.message.message_id
            )

    def _find_submission(self, username: str, image_id: int) -> Optional[int]:
        folders = ["gallery", "scraps"]
        for folder in folders:
            submission_id = self._find_submission_in_folder(username, image_id, folder)
            if submission_id:
                return submission_id
        return None

    def _find_submission_in_folder(self, username: str, image_id: int, folder: str) -> Optional[int]:
        page_listing = self._find_correct_page(username, image_id, folder)
        if not page_listing:
            # No page is valid.
            return None
        return self._find_submission_on_page(image_id, page_listing)

    def _find_submission_on_page(self, image_id: int, page_listing: List[FASubmissionShort]) -> Optional[int]:
        for submission in page_listing:
            test_image_id = self._get_image_id_from_submission(submission)
            if image_id == test_image_id:
                return int(submission.submission_id)
            if test_image_id < image_id:
                return None
        return None

    def _find_correct_page(self, username: str, image_id: int, folder: str) -> Optional[List[FASubmissionShort]]:
        page = 1
        while True:
            listing = self.api.get_user_folder(username, folder, page)
            if len(listing) == 0:
                return None
            last_submission = listing[-1]
            if self._get_image_id_from_submission(last_submission) <= image_id:
                return listing
            page += 1

    def _get_image_id_from_submission(self, submission: FASubmissionShort) -> int:
        image_id = re.split(r"[-.]", submission.thumbnail_url)[-2]
        return int(image_id)