import unittest

from unittest.mock import patch, call

import requests_mock
import telegram
from telegram import Chat

from bot import FASearchBot
from test.util.testTelegramUpdateObjects import MockTelegramUpdate

searchBot = FASearchBot("config-test.json")


class NeatenDirectImageTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    def test_ignore_message(self, bot):
        update = MockTelegramUpdate.with_message(text="hello world")

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_link(self, bot):
        update = MockTelegramUpdate.with_message(text="http://example.com")

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_profile_link(self, bot):
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/user/fender/")

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_journal_link(self, bot):
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/journal/9150534/")

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_direct_link(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
                },
                {
                    "id": post_id-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "download": "dl-{}.jpg".format(post_id),
                "link": "link-{}".format(post_id)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_direct_no_match(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        for folder in ['gallery', 'scraps']:
            r.get(
                "{}/user/{}/{}.json?page=1&full=1".format(searchBot.api_url, username, folder),
                json=[
                    {
                        "id": post_id,
                        "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+4)
                    },
                    {
                        "id": post_id-1,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15)
                    }
                ]
            )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_called_once()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == \
            "Could not locate the image by {} with image id {}.".format(username, image_id)
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_direct_no_match_groupchat(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
            chat_type=Chat.GROUP
        )
        for folder in ['gallery', 'scraps']:
            r.get(
                "{}/user/{}/{}.json?page=1&full=1".format(searchBot.api_url, username, folder),
                json=[
                    {
                        "id": post_id,
                        "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+4)
                    },
                    {
                        "id": post_id-1,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15)
                    }
                ]
            )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_not_called()

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_two_direct_links(self, bot, r):
        username = "fender"
        image_id1 = 1560331512
        image_id2 = 1560331510
        post_id1 = 232347
        post_id2 = 232346
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png "
                 "http://d.facdn.net/art/{0}/{2}/{2}.pic_of_you.png".format(username, image_id1, image_id2)
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id1,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id1)
                },
                {
                    "id": post_id2,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id2)
                },
                {
                    "id": post_id2-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id2-15)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id1),
            json={
                "download": "dl-{}.jpg".format(post_id1),
                "link": "link-{}".format(post_id1)
            }
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id2),
            json={
                "download": "dl-{}.jpg".format(post_id2),
                "link": "link-{}".format(post_id2)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called()
        calls = [call(
            chat_id=update.message.chat_id,
            photo="dl-{}.jpg".format(post_id),
            caption="link-{}".format(post_id),
            reply_to_message_id=update.message.message_id
        ) for post_id in [post_id1, post_id2]]
        bot.send_photo.assert_has_calls(calls)

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_duplicate_direct_link(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png ".format(username, image_id)*2
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
                },
                {
                    "id": post_id-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "download": "dl-{}.jpg".format(post_id),
                "link": "link-{}".format(post_id)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_direct_link_and_matching_submission_link(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png https://furaffinity.net/view/{2}/".format(
                username, image_id, post_id
            )
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
                },
                {
                    "id": post_id-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "download": "dl-{}.jpg".format(post_id),
                "link": "link-{}".format(post_id)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_direct_link_and_different_submission_link(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id1 = 232347
        post_id2 = 233447
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png https://furaffinity.net/view/{2}/".format(
                username, image_id, post_id2
            )
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id2,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+300)
                },
                {
                    "id": post_id1,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
                },
                {
                    "id": post_id1-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15)
                }
            ]
        )
        for post_id in [post_id1, post_id2]:
            r.get(
                "{}/submission/{}.json".format(searchBot.api_url, post_id),
                json={
                    "download": "dl-{}.jpg".format(post_id),
                    "link": "link-{}".format(post_id)
                }
            )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called()
        calls = [call(
            chat_id=update.message.chat_id,
            photo="dl-{}.jpg".format(post_id),
            caption="link-{}".format(post_id),
            reply_to_message_id=update.message.message_id
        ) for post_id in [post_id1, post_id2]]
        bot.send_photo.assert_has_calls(calls)

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_submission_link_and_different_direct_link(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id1 = 232347
        post_id2 = 233447
        update = MockTelegramUpdate.with_message(
            text="https://furaffinity.net/view/{2}/ http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(
                username, image_id, post_id2
            )
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id2,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+300)
                },
                {
                    "id": post_id1,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
                },
                {
                    "id": post_id1-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15)
                }
            ]
        )
        for post_id in [post_id1, post_id2]:
            r.get(
                "{}/submission/{}.json".format(searchBot.api_url, post_id),
                json={
                    "download": "dl-{}.jpg".format(post_id),
                    "link": "link-{}".format(post_id)
                }
            )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called()
        calls = [call(
            chat_id=update.message.chat_id,
            photo="dl-{}.jpg".format(post_id),
            caption="link-{}".format(post_id),
            reply_to_message_id=update.message.message_id
        ) for post_id in [post_id2, post_id1]]
        bot.send_photo.assert_has_calls(calls)
