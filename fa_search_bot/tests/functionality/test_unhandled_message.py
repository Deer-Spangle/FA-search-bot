import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.unhandled import UnhandledMessageFunctionality
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, ChatType


@pytest.mark.asyncio
async def test_unhandled_message(mock_client):
    event = MockTelegramEvent.with_message(
        text="Hello can I have a picture"
    )
    unhandled = UnhandledMessageFunctionality()

    with pytest.raises(StopPropagation):
        await unhandled.call(event)

    event.reply.assert_called_with(
        "Sorry, I'm not sure how to handle that message",
    )


@pytest.mark.asyncio
async def test_unhandled_group_message(mock_client):
    event = MockTelegramEvent.with_message(
        text="Hey friendo, how are you?",
        chat_type=ChatType.GROUP
    )
    unhandled = UnhandledMessageFunctionality()

    await unhandled.call(event)

    event.reply.assert_not_called()
