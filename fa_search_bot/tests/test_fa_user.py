import unittest

from fa_search_bot.fa_submission import FAUser


class FAUserTest(unittest.TestCase):

    def test_constructor(self):
        name = "John"
        profile_name = "john"

        author = FAUser(name, profile_name)

        assert author.name == name
        assert author.profile_name == profile_name
        assert f"/user/{profile_name}" in author.link

    def test_from_short_dict(self):
        name = "John"
        profile_name = "john"

        author = FAUser.from_short_dict(
            {
                "name": name,
                "profile_name": profile_name
            }
        )

        assert author.name == name
        assert author.profile_name == profile_name
        assert f"/user/{profile_name}" in author.link

    def test_from_submission_dict(self):
        name = "John"
        profile_name = "john"

        author = FAUser.from_submission_dict(
            {
                "name": name,
                "profile_name": profile_name
            }
        )

        assert author.name == name
        assert author.profile_name == profile_name
        assert f"/user/{profile_name}" in author.link