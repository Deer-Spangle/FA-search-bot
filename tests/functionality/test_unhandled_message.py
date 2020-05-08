from telegram import Chat

from functionalities.unhandled import UnhandledMessageFunctionality
from tests.util.mock_telegram_update import MockTelegramUpdate


def test_unhandled_message(context):
    update = MockTelegramUpdate.with_message(
        text="Hello can I have a picture"
    )
    unhandled = UnhandledMessageFunctionality()

    unhandled.call(update, context)

    context.bot.send_message.assert_called_with(
        chat_id=update.message.chat_id,
        text="Sorry, I'm not sure how to handle that message"
    )


def test_unhandled_group_message(context):
    update = MockTelegramUpdate.with_message(
        text="Hey friendo, how are you?",
        chat_type=Chat.GROUP
    )
    unhandled = UnhandledMessageFunctionality()

    unhandled.call(update, context)

    context.bot.send_message.assert_not_called()
