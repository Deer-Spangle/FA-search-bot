import pytest
from telethon.events import StopPropagation

from fa_search_bot.bot import ImageHashRecommendFunctionality
from fa_search_bot.tests.util.mock_telegram_event import (ChatType,
                                                          MockTelegramEvent)


@pytest.mark.asyncio
async def test_sends_recommendation(mock_client):
    event = MockTelegramEvent.with_message(text=None).with_photo()
    func = ImageHashRecommendFunctionality()

    with pytest.raises(StopPropagation):
        await func.call(event)

    event.reply.assert_called()
    message_text = event.reply.call_args[0][0]
    assert "@FindFurryPicBot" in message_text
    assert "@FoxBot" in message_text
    assert "@reverseSearchBot" in message_text


@pytest.mark.asyncio
async def test_no_reply_in_group(mock_client):
    event = MockTelegramEvent.with_message(
        text=None,
        chat_type=ChatType.GROUP
    ).with_photo()
    func = ImageHashRecommendFunctionality()

    await func.call(event)

    event.reply.assert_not_called()
