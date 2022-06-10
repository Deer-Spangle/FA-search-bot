import unittest

from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, _MockDocument


class MockObjectsTest(unittest.TestCase):
    def test_cannot_create_update(self):
        try:
            MockTelegramEvent()
            assert False, "Should have failed to create."
        except NotImplementedError:
            pass

    def test_can_create_message(self):
        event = MockTelegramEvent.with_message()
        assert event.callback_query is None
        assert event.message is not None
        assert event.message.message_id is not None
        assert event.message.chat_id is not None
        assert isinstance(event.message.photo, list)
        assert len(event.message.photo) == 0

    def test_can_create_message_with_photo(self):
        event = MockTelegramEvent.with_message().with_photo()
        assert event.callback_query is None
        assert event.message is not None
        assert event.message.message_id is not None
        assert event.message.chat_id is not None
        assert isinstance(event.message.photo, list)
        assert len(event.message.photo) == 1
        assert event.message.photo[0]["file_id"] is not None

    def test_can_create_message_with_document(self):
        event = MockTelegramEvent.with_message().with_document()
        assert event.callback_query is None
        assert event.message is not None
        assert event.message.message_id is not None
        assert event.message.chat_id is not None
        assert isinstance(event.message.photo, list)
        assert len(event.message.photo) == 0
        assert event.message.document is not None
        assert isinstance(event.message.document, _MockDocument)
        assert event.message.document.file_id is not None
        assert event.message.document.mime_type is None

    def test_can_create_callback(self):
        event = MockTelegramEvent.with_callback_query(b"example")
        assert event.data == b"example"
        assert event.original_update is None

    def test_can_create_callback_with_message(self):
        event = MockTelegramEvent.with_callback_query(b"data").with_inline_id(5, 17, 123)
        assert event.data == b"data"
        assert event.original_update is not None
        assert event.original_update.msg_id is not None
        assert event.original_update.msg_id.dc_id == 5
        assert event.original_update.msg_id.id == 17
        assert event.original_update.msg_id.access_hash == 123
