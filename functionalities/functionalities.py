from abc import ABC, abstractmethod

import telegram
from telegram.ext import CallbackContext


class BotFunctionality(ABC):

    def __init__(self, handler_cls, **kwargs):
        self.kwargs = kwargs
        self.handler_cls = handler_cls

    def register(self, dispatcher):
        args_dict = self.kwargs
        args_dict["callback"] = self.call
        handler = self.handler_cls(**args_dict)
        dispatcher.add_handler(handler)

    @abstractmethod
    def call(self, update: telegram.Update, context: CallbackContext):
        pass
