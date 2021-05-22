from telegram import Chat

from fa_search_bot.bot import ImageHashRecommendFunctionality
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


def test_sends_recommendation(context):
    update = MockTelegramEvent.with_message(text=None).with_photo()
    func = ImageHashRecommendFunctionality()

    func.call(update, context)

    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    message_text = context.bot.send_message.call_args[1]['text']
    assert "@FindFurryPicBot" in message_text
    assert "@FoxBot" in message_text
    assert "@reverseSearchBot" in message_text


def test_no_reply_in_group(context):
    update = MockTelegramEvent.with_message(
        text=None,
        chat_type=Chat.GROUP
    ).with_photo()
    func = ImageHashRecommendFunctionality()

    func.call(update, context)

    context.bot.send_message.assert_not_called()
