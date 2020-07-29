from telegram.ext import Filters, BaseFilter


class FilterRegex(Filters.regex):

    def filter(self, message):
        text = message.text_markdown_urled or message.caption_markdown_urled
        if text:
            return bool(self.pattern.search(text))
        return False


class FilterImageNoCaption(BaseFilter):

    def filter(self, message):
        text = message.text_markdown_urled or message.caption_markdown_urled
        return not text and bool(message.photo)
