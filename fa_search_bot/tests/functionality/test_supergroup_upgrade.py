import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.supergroup_upgrade import (
    SupergroupUpgradeFunctionality,
)
from fa_search_bot.subscription_watcher import SubscriptionWatcher
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_supergroup_upgrade(mock_client):
    old_chat_id = 12345
    new_chat_id = 54321
    event = MockTelegramEvent.with_migration(
        old_chat_id=old_chat_id, new_chat_id=new_chat_id
    )
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SupergroupUpgradeFunctionality(watcher)
    migrate_chat = MockMethod("Migrate subscriptions")
    watcher.migrate_chat = migrate_chat.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert migrate_chat.called
    assert migrate_chat.args is not None
    assert migrate_chat.args[0] == -12345
    assert migrate_chat.args[1] == -10054321
    event.reply.assert_not_called()
