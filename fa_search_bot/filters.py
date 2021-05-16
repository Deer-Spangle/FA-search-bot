from telegram import Message
from telegram.ext import Filters, BaseFilter
from telethon.events import NewMessage


class FilterRegex(Filters.regex):

    def filter(self, message: Message) -> bool:
        text = message.text_markdown_urled or message.caption_markdown_urled
        if text and self.pattern.search(text):
            return True
        buttons = [[]]
        if message.reply_markup and message.reply_markup.inline_keyboard:
            buttons = message.reply_markup.inline_keyboard
        for button_row in buttons:
            for button in button_row:
                if button.text and self.pattern.search(button.text):
                    return True
                if button.url and self.pattern.search(button.url):
                    return True
        return False


def filter_image_no_caption(event: NewMessage.Event) -> bool:
    keyboard = event.message.buttons
    has_buttons = False
    if keyboard:
        has_buttons = any(bool(button.url) for button_row in keyboard for button in button_row)
    text = event.message.text
    media = event.message.photo or event.message.document
    return not (text or has_buttons) and media
