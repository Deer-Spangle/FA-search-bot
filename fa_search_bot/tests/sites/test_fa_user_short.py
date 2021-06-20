import unittest

from fa_search_bot.sites.fa_submission import FAUserShort


class FAUserShortTest(unittest.TestCase):

    def test_constructor(self):
        name = "John"
        profile_name = "john"

        author = FAUserShort(name, profile_name)

        assert author.name == name
        assert author.profile_name == profile_name
        assert f"/user/{profile_name}" in author.link