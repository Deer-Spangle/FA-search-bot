import unittest

from tests.util.mock_telegram_update import MockTelegramUpdate, _MockDocument


class MockObjectsTest(unittest.TestCase):

    def test_cannot_create_update(self):
        try:
            MockTelegramUpdate()
            assert False, "Should have failed to create."
        except NotImplementedError:
            pass

    def test_can_create_message(self):
        update = MockTelegramUpdate.with_message()
        assert update.callback_query is None
        assert update.message is not None
        assert update.message.message_id is not None
        assert update.message.chat_id is not None
        assert isinstance(update.message.photo, list)
        assert len(update.message.photo) == 0

    def test_can_create_message_with_photo(self):
        update = MockTelegramUpdate.with_message().with_photo()
        assert update.callback_query is None
        assert update.message is not None
        assert update.message.message_id is not None
        assert update.message.chat_id is not None
        assert isinstance(update.message.photo, list)
        assert len(update.message.photo) == 1
        assert update.message.photo[0]["file_id"] is not None

    def test_can_create_message_with_document(self):
        update = MockTelegramUpdate.with_message().with_document()
        assert update.callback_query is None
        assert update.message is not None
        assert update.message.message_id is not None
        assert update.message.chat_id is not None
        assert isinstance(update.message.photo, list)
        assert len(update.message.photo) == 0
        assert update.message.document is not None
        assert isinstance(update.message.document, _MockDocument)
        assert update.message.document.file_id is not None
        assert update.message.document.mime_type is None

    def test_can_create_callback(self):
        update = MockTelegramUpdate.with_callback_query()
        assert update.message is None
        assert update.callback_query is not None
        assert update.callback_query.message is None

    def test_can_create_callback_with_message(self):
        update = MockTelegramUpdate.with_callback_query().with_originating_message()
        assert update.message is None
        assert update.callback_query is not None
        assert update.callback_query.message is not None
        assert update.callback_query.message.message_id is not None
        assert update.callback_query.message.chat_id is not None

    def test_can_create_command(self):
        update = MockTelegramUpdate.with_command()
        assert update.callback_query is None
        assert update.message is not None
        assert update.message.message_id is not None
        assert update.message.chat_id is not None
