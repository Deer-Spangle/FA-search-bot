import uuid
from asyncio import Future
from typing import Optional, List, Dict
from unittest.mock import MagicMock, Mock, AsyncMock

from telegram import Chat


def generate_key():
    return str(uuid.uuid4())


PhotoType = List[Dict]


class MockTelegramEvent:

    def __init__(self):
        if self.__class__ == MockTelegramEvent:
            raise NotImplementedError()
        self.message = None
        self.channel_post = None
        self.callback_query = None

    respond = AsyncMock()

    @staticmethod
    def with_message(
            message_id=None,
            chat_id=None,
            text: str = None,
            text_markdown_urled: str = None,
            chat_type=Chat.PRIVATE,
            migrate_from_chat_id: int = None,
            migrate_to_chat_id: int = None
    ):
        return _MockTelegramMessage(
            message_id=message_id,
            chat_id=chat_id,
            text=text,
            text_markdown_urled=text_markdown_urled,
            chat_type=chat_type,
            migrate_from_chat_id=migrate_from_chat_id,
            migrate_to_chat_id=migrate_to_chat_id,
        )

    @staticmethod
    def with_channel_post(message_id: Optional[int] = None, chat_id: Optional[int] = None, text: Optional[str] = None):
        return _MockTelegramChannelPost(
            message_id=message_id,
            chat_id=chat_id,
            text=text
        )

    @classmethod
    def with_callback_query(cls, data=None):
        return _MockTelegramCallback(
            data=data
        )

    @classmethod
    def with_command(cls, message_id=None, chat_id=None):
        return _MockTelegramCommand(
            message_id=message_id,
            chat_id=chat_id
        )

    @classmethod
    def with_inline_query(cls, query_id=None, query=None, offset=None):
        return _MockTelegramInlineQuery(
            query_id=query_id,
            query=query,
            offset=offset
        )


class _MockTelegramMessage(MockTelegramEvent):

    def __init__(
            self,
            *,
            message_id=None,
            text: str = None,
            text_markdown_urled: str = None,
            chat_id=None,
            chat_type=None,
            migrate_from_chat_id: int = None,
            migrate_to_chat_id: int = None
    ):
        super().__init__()
        # Set up message data
        self.message = _MockMessage(
            message_id=message_id,
            chat_id=chat_id,
            text=text,
            text_markdown_urled=text_markdown_urled,
            chat_type=chat_type,
            migrate_from_chat_id=migrate_from_chat_id,
            migrate_to_chat_id=migrate_to_chat_id
        )

    def with_photo(self, photo_file_id=None, caption: str = None, caption_markdown_urled: str = None):
        self.message.set_photo(photo_file_id, caption, caption_markdown_urled)
        return self

    def with_document(self, file_id=None, mime_type=None):
        self.message.set_document(file_id, mime_type)
        return self

    def with_buttons(self, buttons: List[List['MockButton']]):
        self.message.set_keyboard(buttons)
        return self


class _MockTelegramChannelPost(MockTelegramEvent):

    def __init__(self, message_id: Optional[int] = None, chat_id: Optional[int] = None, text: Optional[str] = None):
        super().__init__()
        self.channel_post = _MockChannelPost(
            message_id=message_id,
            chat_id=chat_id,
            text=text
        )


class _MockTelegramCallback(MockTelegramEvent):

    def __init__(self, *, data=None):
        super().__init__()
        self.callback_query = _MockCallback(data)

    def with_originating_message(self, message_id=None, chat_id=None):
        self.callback_query.set_message(message_id, chat_id)
        return self


class _MockTelegramCommand(MockTelegramEvent):

    def __init__(self, *, message_id=None, chat_id=None):
        super().__init__()
        self.message = _MockMessage(
            message_id=message_id,
            chat_id=chat_id
        )


class _MockTelegramInlineQuery(MockTelegramEvent):

    def __init__(self, *, query_id=None, query=None, offset=None):
        super().__init__()
        self.inline_query = _MockInlineQuery(query_id=query_id, query=query, offset=offset)


class _MockInlineQuery:

    def __init__(self, *, query_id=None, query=None, offset=None):
        self.id = query_id
        self.query = query
        self.offset = offset
        # Set defaults
        if query_id is None:
            self.id = generate_key()
        if offset is None:
            self.offset = ""


class _MockMessage:

    def __init__(
            self,
            *,
            message_id=None,
            chat_id=None,
            text: str = None,
            text_markdown_urled: str = None,
            chat_type=None,
            migrate_from_chat_id: int = None,
            migrate_to_chat_id: int = None
    ):
        self.message_id = message_id
        self.chat_id = chat_id
        self.text = text
        self.text_markdown_urled = text_markdown_urled or text
        self.chat = _MockChat(chat_type=chat_type)
        self.migrate_from_chat_id = migrate_from_chat_id
        self.migrate_to_chat_id = migrate_to_chat_id
        # Set defaults
        self.photo: PhotoType = []
        self.caption: Optional[str] = None
        self.caption_markdown_urled: Optional[str] = None
        self.document = None
        self.reply_markup = None
        if message_id is None:
            self.message_id = generate_key()
        if chat_id is None:
            self.chat_id = generate_key()
        if text_markdown_urled is None:
            self.text_markdown_urled = self.text

    def set_photo(self, photo_file_id, caption: str = None, caption_markdown_urled: str = None):
        # Defaults
        if photo_file_id is None:
            photo_file_id = generate_key()
        # Set values
        self.photo.append({"file_id": photo_file_id})
        self.caption = caption
        self.caption_markdown_urled = caption_markdown_urled or caption

    def set_document(self, file_id, mime_type):
        self.document = _MockDocument(
            file_id,
            mime_type
        )

    def set_keyboard(self, buttons: List[List['MockButton']]):
        self.reply_markup = _MockKeyboard(buttons)


class _MockChannelPost:

    def __init__(
            self,
            *,
            message_id: Optional[int] = None,
            chat_id: Optional[int] = None,
            text: Optional[str] = None,
            text_markdown_urled: Optional[str] = None
    ):
        self.message_id = message_id
        self.chat_id = chat_id
        self.text = text
        self.text_markdown_urled = text_markdown_urled or text
        self.chat = _MockChannel()
        # Set defaults
        if message_id is None:
            self.message_id = generate_key()
        if chat_id is None:
            self.chat_id = "-100" + generate_key()
        if text_markdown_urled is None:
            self.text_markdown_urled = self.text


class _MockChat:

    def __init__(self, chat_type=None):
        self.type = chat_type


class _MockChannel(_MockChat):

    def __init__(self):
        super().__init__(chat_type=Chat.CHANNEL)


class _MockDocument:

    def __init__(self, file_id=None, mime_type=None):
        self.file_id = file_id
        self.mime_type = mime_type
        # Set defaults
        if file_id is None:
            self.file_id = generate_key()


class _MockCallback:

    def __init__(self, data=None):
        self.data = data
        self.message = None

    def set_message(self, message_id, chat_id):
        self.message = _MockMessage(message_id=message_id, chat_id=chat_id)


class _MockKeyboard:

    def __init__(self, buttons: List[List['MockButton']]):
        self.inline_keyboard = buttons


class MockButton:

    def __init__(self, text: str, url: str):
        self.text = text
        self.url = url
