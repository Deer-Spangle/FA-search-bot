from fa_search_bot.functionalities.supergroup_upgrade import SupergroupUpgradeFunctionality
from fa_search_bot.subscription_watcher import SubscriptionWatcher
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_telegram_update import MockTelegramUpdate


def test_supergroup_upgrade_old_chat(context):
    old_chat_id = 12345
    new_chat_id = 54321
    update = MockTelegramUpdate.with_message(chat_id=new_chat_id, migrate_from_chat_id=old_chat_id)
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = SupergroupUpgradeFunctionality(watcher)
    migrate_chat = MockMethod("Migrate subscriptions")
    watcher.migrate_chat = migrate_chat.call

    func.call(update, context)

    assert migrate_chat.called
    assert migrate_chat.args is not None
    assert migrate_chat.args[0] == old_chat_id
    assert migrate_chat.args[1] == new_chat_id
    context.bot.send_message.assert_not_called()


def test_supergroup_upgrade_new_chat(context):
    old_chat_id = 12345
    new_chat_id = 54321
    update = MockTelegramUpdate.with_message(chat_id=old_chat_id, migrate_to_chat_id=new_chat_id)
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = SupergroupUpgradeFunctionality(watcher)
    migrate_chat = MockMethod("Migrate subscriptions")
    watcher.migrate_chat = migrate_chat.call

    func.call(update, context)

    assert migrate_chat.called
    assert migrate_chat.args is not None
    assert migrate_chat.args[0] == old_chat_id
    assert migrate_chat.args[1] == new_chat_id
    context.bot.send_message.assert_not_called()
