from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import re

    from telethon.events import NewMessage


def filter_regex(event: NewMessage.Event, pattern: re.Pattern) -> bool:
    text = event.message.text
    if text and pattern.search(text):
        return True
    if event.message.buttons:
        for button_row in event.message.buttons:
            for button in button_row:
                if button.text and pattern.search(button.text):
                    return True
                if button.url and pattern.search(button.url):
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
