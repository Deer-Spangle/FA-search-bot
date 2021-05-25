import pytest
from telethon.events import StopPropagation

from fa_search_bot.bot import FASearchBot
from fa_search_bot.functionalities.welcome import WelcomeFunctionality
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_welcome_message(mock_client):
    event = MockTelegramEvent.with_message(text="/start")
    func = WelcomeFunctionality()

    with pytest.raises(StopPropagation):
        await func.call(event)

    event.respond.assert_called()
    message_text = event.respond.call_args[0][0]
    assert "@deerspangle" in message_text
    assert "https://github.com/Deer-Spangle/FA-search-bot" in message_text
    assert FASearchBot.VERSION in message_text
