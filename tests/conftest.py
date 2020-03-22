from unittest.mock import MagicMock

import pytest


@pytest.fixture
def context():
    context = MagicMock()
    context.bot = MagicMock()
    return context
