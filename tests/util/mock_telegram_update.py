import uuid

from telegram import Chat


def generate_key():
    return str(uuid.uuid4())


class MockTelegramUpdate:

    def __init__(self):
        if self.__class__ == MockTelegramUpdate:
            raise NotImplementedError()
        self.message = None
        self.callback_query = None

    @staticmethod
    def with_message(message_id=None, chat_id=None, text=None, text_markdown_urled=None, chat_type=Chat.PRIVATE):
        return _MockTelegramMessage(
            message_id=message_id,
            chat_id=chat_id,
            text=text,
            text_markdown_urled=text_markdown_urled,
            chat_type=chat_type
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


class _MockTelegramMessage(MockTelegramUpdate):

    def __init__(self, *, message_id=None, text=None, text_markdown_urled=None, chat_id=None, chat_type=None):
        super().__init__()
        # Set up message data
        self.message = _MockMessage(
            message_id=message_id,
            chat_id=chat_id,
            text=text,
            text_markdown_urled=text_markdown_urled,
            chat_type=chat_type
        )

    def with_photo(self, photo_file_id=None, caption=None):
        self.message.set_photo(photo_file_id, caption)
        return self

    def with_document(self, file_id=None, mime_type=None):
        self.message.set_document(file_id, mime_type)
        return self


class _MockTelegramCallback(MockTelegramUpdate):

    def __init__(self, *, data=None):
        super().__init__()
        self.callback_query = _MockCallback(data)

    def with_originating_message(self, message_id=None, chat_id=None):
        self.callback_query.set_message(message_id, chat_id)
        return self


class _MockTelegramCommand(MockTelegramUpdate):

    def __init__(self, *, message_id=None, chat_id=None):
        super().__init__()
        self.message = _MockMessage(
            message_id=message_id,
            chat_id=chat_id
        )


class _MockTelegramInlineQuery(MockTelegramUpdate):

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

    def __init__(self, *, message_id=None, chat_id=None, text=None, text_markdown_urled=None, chat_type=None):
        self.message_id = message_id
        self.chat_id = chat_id
        self.text = text
        self.text_markdown_urled = text_markdown_urled or text
        self.chat = _MockChat(chat_type=chat_type)
        # Set defaults
        self.photo = []
        self.caption = None
        self.document = None
        if message_id is None:
            self.message_id = generate_key()
        if chat_id is None:
            self.chat_id = generate_key()
        if text_markdown_urled is None:
            self.text_markdown_urled = self.text

    def set_photo(self, photo_file_id, caption):
        # Defaults
        if photo_file_id is None:
            photo_file_id = generate_key()
        # Set values
        self.photo.append({"file_id": photo_file_id})
        self.caption = caption

    def set_document(self, file_id, mime_type):
        self.document = _MockDocument(
            file_id,
            mime_type
        )


class _MockChat:

    def __init__(self, chat_type=None):
        self.type = chat_type


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
