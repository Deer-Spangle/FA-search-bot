from unittest.mock import Mock

import pytest
from telegram import Bot
from telegram.ext import CallbackContext


@pytest.fixture
def context():
    context = Mock(CallbackContext)
    context.attach_mock(Mock(Bot), "bot")
    context.bot = Mock(Bot)
    return context
