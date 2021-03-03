from telegram.ext import Filters, BaseFilter


class FilterRegex(Filters.regex):

    def filter(self, message):
        text = message.text_markdown_urled or message.caption_markdown_urled
        if text and self.pattern.search(text):
            return True
        buttons = message.reply_markup.inline_keyboard or [[]]
        for button_row in buttons:
            for button in button_row:
                if button.text and self.pattern.search(button.text):
                    return True
                if button.url and self.pattern.search(button.url):
                    return True
        return False


class FilterImageNoCaption(BaseFilter):

    def filter(self, message):
        text = message.text_markdown_urled or message.caption_markdown_urled
        return not text and bool(message.photo)
