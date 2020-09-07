from abc import ABC, abstractmethod
from typing import Optional, List

import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.subscription_watcher import Subscription, SubscriptionWatcher


class MenuFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(CommandHandler, command='menu')

    def call(self, update: telegram.Update, context: CallbackContext):
        menu = RootMenu()
        menu.send_reply(update, context)


class MenuCallbackFunctionality(BotFunctionality):

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(CallbackQueryHandler)
        self.watcher = watcher

    def call(self, update: telegram.Update, context: CallbackContext):
        menus = [
            RootMenu(),
            HelpMenu(),
            SubscriptionsMenu(),
            SubscriptionAddMenu(),
            SubscriptionRemoveMenu(list(self.watcher.subscriptions))  # TODO: not this.
        ]
        for menu in menus:
            if update.callback_query.data == menu.callback:
                return menu.edit_message(update, context)
            if update.callback_query.data.startswith(menu.callback+":"):
                return menu.handle_callback(update, context)


class Menu(ABC):
    @abstractmethod
    def text(self) -> str:
        pass

    @abstractmethod
    def keyboard(self) -> Optional[InlineKeyboardMarkup]:
        pass

    def send_reply(self, update: telegram.Update, context: CallbackContext):
        context.bot.send_message(
            update.message.chat_id,
            self.text(),
            reply_to_message_id=update.message.message_id,
            reply_markup=self.keyboard()
        )

    def edit_message(self, update: telegram.Update, context: CallbackContext):
        context.bot.edit_message_text(
            self.text(),
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=self.keyboard()
        )
        pass

    def handle_callback(self, update: telegram.Update, context: CallbackContext):
        pass


class RootMenu(Menu):
    callback = "menu"
    back_only = InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=callback)]])

    def text(self) -> str:
        return "Welcome to the FA SearchB Bot main menu\nWhat would you like to do?"

    def keyboard(self) -> Optional[InlineKeyboardMarkup]:
        buttons = [
            [InlineKeyboardButton("Help", callback_data=HelpMenu.callback)],
            [InlineKeyboardButton("Subscriptions", callback_data=SubscriptionsMenu.callback)]
        ]
        return InlineKeyboardMarkup(buttons)


class HelpMenu(Menu):
    callback = "help"

    def text(self) -> str:
        return "Help"

    def keyboard(self) -> Optional[InlineKeyboardMarkup]:
        return RootMenu.back_only


class SubscriptionsMenu(Menu):
    callback = "subs"

    def text(self) -> str:
        return "Subscriptions"

    def keyboard(self) -> Optional[InlineKeyboardMarkup]:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Add subscription", callback_data=SubscriptionAddMenu.callback)],
            # [InlineKeyboardButton("Edit subscription", callback_data=SubscriptionEditMenu.callback)],
            [InlineKeyboardButton("Remove subscription", callback_data=SubscriptionRemoveMenu.callback)]
        ])


class SubscriptionAddMenu(Menu):
    callback = "subs-add"

    def text(self) -> str:
        pass

    def keyboard(self) -> Optional[InlineKeyboardMarkup]:
        pass


class SubscriptionRemoveMenu(Menu):
    callback = "subs-remove"

    def __init__(self, subscriptions: List[Subscription]):
        self.subscriptions = subscriptions

    def text(self) -> str:
        return "Which subscription would you like to remove?"

    def keyboard(self) -> Optional[InlineKeyboardMarkup]:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(sub.query_str, callback_data=self.callback+":AAA")]
            for sub in self.subscriptions
        ])

    def handle_callback(self, update: telegram.Update, context: CallbackContext):
        print(f"Removing subscription: {update.callback_query.data}")
