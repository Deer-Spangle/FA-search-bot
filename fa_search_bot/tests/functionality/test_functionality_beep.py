import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.beep import BeepFunctionality
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_beep(context):
    event = MockTelegramEvent.with_command()
    beep = BeepFunctionality()

    with pytest.raises(StopPropagation):
        await beep.call(event)

    event.respond.assert_called()
    assert event.respond.call_args[0][0] == "boop"
