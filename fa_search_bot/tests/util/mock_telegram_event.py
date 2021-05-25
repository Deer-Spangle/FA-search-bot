import uuid
from enum import Enum, auto
from typing import Optional, List, Dict
from unittest.mock import AsyncMock, Mock

from telegram import Chat
from telethon import TelegramClient


def generate_key():
    return str(uuid.uuid4())


PhotoType = List[Dict]


class ChatType(Enum):
    PRIVATE = auto()
    GROUP = auto()
    CHANNEL = auto()


class MockTelegramEvent:

    def __init__(self):
        if self.__class__ == MockTelegramEvent:
            raise NotImplementedError()
        self.message = None
        self.channel_post = None
        self.callback_query = None
        self.client = Mock(TelegramClient)
        self.respond = AsyncMock()
        self.reply = AsyncMock()

    @staticmethod
    def with_message(
            message_id: Optional[int] = None,
            chat_id: Optional[int] = None,
            text: Optional[str] = None,
            chat_type: ChatType = ChatType.PRIVATE,
            migrate_from_chat_id: Optional[int] = None,
            migrate_to_chat_id: Optional[int] = None,
            client: Optional[TelegramClient] = None,
    ) -> '_MockTelegramMessage':
        return _MockTelegramMessage(
            message_id=message_id,
            chat_id=chat_id,
            text=text,
            chat_type=chat_type,
            migrate_from_chat_id=migrate_from_chat_id,
            migrate_to_chat_id=migrate_to_chat_id,
            client=client,
        )

    @staticmethod
    def with_channel_post(message_id: Optional[int] = None, chat_id: Optional[int] = None, text: Optional[str] = None):
        return _MockTelegramMessage(
            message_id=message_id,
            chat_id=chat_id,
            chat_type=ChatType.CHANNEL,
            text=text
        )

    @classmethod
    def with_callback_query(cls, data=None):
        return _MockTelegramCallback(
            data=data
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
            message_id: Optional[int] = None,
            text: Optional[str] = None,
            chat_id: Optional[int] = None,
            chat_type: ChatType = ChatType.PRIVATE,
            migrate_from_chat_id: Optional[int] = None,
            migrate_to_chat_id: Optional[int] = None,
            client: Optional[TelegramClient] = None,
    ):
        super().__init__()
        # Set up message data
        self.message = _MockMessage(
            message_id=message_id,
            chat_id=chat_id,
            text=text,
            chat_type=chat_type,
            migrate_from_chat_id=migrate_from_chat_id,
            migrate_to_chat_id=migrate_to_chat_id
        )
        if client is not None:
            self.client = client

    def with_photo(self, photo_file_id=None, caption: str = None):
        self.message.set_photo(photo_file_id, caption)
        return self

    def with_document(self, file_id=None, mime_type=None):
        self.message.set_document(file_id, mime_type)
        return self

    def with_buttons(self, buttons: List[List['MockButton']]):
        self.message.set_keyboard(buttons)
        return self

    @property
    def text(self):
        return self.message.text

    @property
    def chat_id(self):
        return self.message.chat_id

    @property
    def is_private(self):
        return self.message.is_private

    @property
    def is_group(self):
        return self.message.is_group

    @property
    def is_channel(self):
        return self.message.is_channel

    @property
    def input_chat(self):
        return self.message.input_chat


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
        self.query = _MockInlineQuery(query_id=query_id, query=query, offset=offset)
        self.answer = AsyncMock()
        self.builder = _MockInlineBuilder()


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


class _MockInlineBuilder:

    async def photo(self, *args, **kwargs):
        return self._MockInlinePhoto(
            *args,
            **kwargs
        )

    async def article(self, *args, **kwargs):
        return self._MockInlineArticle(
            *args,
            **kwargs
        )

    class _MockInlineResult:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class _MockInlinePhoto(_MockInlineResult):
        pass

    class _MockInlineArticle(_MockInlineResult):
        pass


class _MockMessage:

    def __init__(
            self,
            *,
            message_id: Optional[int] = None,
            text: Optional[str] = None,
            chat_id: Optional[int] = None,
            chat_type: ChatType = ChatType.PRIVATE,
            migrate_from_chat_id: Optional[int] = None,
            migrate_to_chat_id: Optional[int] = None
    ):
        self.id = message_id
        self.chat_id = chat_id
        self.text = text
        self.input_chat = _MockChat(chat_type=chat_type)
        self.is_private = chat_type == ChatType.PRIVATE
        self.is_group = chat_type == ChatType.GROUP
        self.is_channel = chat_type == ChatType.CHANNEL
        self.migrate_from_chat_id = migrate_from_chat_id
        self.migrate_to_chat_id = migrate_to_chat_id
        # Set defaults
        self.photo: PhotoType = []
        self.document = None
        self.buttons = None
        if message_id is None:
            self.message_id = generate_key()
        if chat_id is None:
            self.chat_id = generate_key()

    def set_photo(self, photo_file_id, caption: str = None):
        # Defaults
        if photo_file_id is None:
            photo_file_id = generate_key()
        # Set values
        self.photo.append({"file_id": photo_file_id})
        self.text = caption

    def set_document(self, file_id, mime_type):
        self.document = _MockDocument(
            file_id,
            mime_type
        )

    def set_keyboard(self, buttons: List[List['MockButton']]):
        self.buttons = buttons


class _MockChannelPost:

    def __init__(
            self,
            *,
            message_id: Optional[int] = None,
            chat_id: Optional[int] = None,
            text: Optional[str] = None,
    ):
        self.message_id = message_id
        self.chat_id = chat_id
        self.text = text
        self.chat = _MockChannel()
        # Set defaults
        if message_id is None:
            self.message_id = generate_key()
        if chat_id is None:
            self.chat_id = "-100" + generate_key()


class _MockChat:

    def __init__(self, chat_type: ChatType = ChatType.PRIVATE):
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


class MockButton:

    def __init__(self, text: str, url: str):
        self.text = text
        self.url = url
