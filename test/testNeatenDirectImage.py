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
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id),
                    "link": "link-view/{}".format(post_id)
                },
                {
                    "id": post_id-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15),
                    "link": "link-view/{}".format(post_id-1)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": '512'
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "http://example.com/dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-view/{}".format(post_id)
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
                        "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+4),
                    "link": "link-view/{}".format(post_id)
                    },
                    {
                        "id": post_id-1,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15),
                    "link": "link-view/{}".format(post_id-1)
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
                        "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+4),
                        "link": "link-view/{}".format(post_id)
                    },
                    {
                        "id": post_id-1,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15),
                        "link": "link-view/{}".format(post_id-1)
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
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id1),
                    "link": "link-view/{}".format(post_id1)
                },
                {
                    "id": post_id2,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id2),
                    "link": "link-view/{}".format(post_id2)
                },
                {
                    "id": post_id2-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id2-15),
                    "link": "link-view/{}".format(post_id2-1)
                }
            ]
        )
        for post_id, image_id in [(post_id1, image_id1), (post_id2, image_id2)]:
            r.get(
                "{}/submission/{}.json".format(searchBot.api_url, post_id),
                json={
                    "full": "http://example.com/dl-{}.jpg".format(post_id),
                    "download": "http://example.com/dl-{}.jpg".format(post_id),
                    "link": "link-view/{}".format(post_id),
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
                }
            )
            r.head(
                "http://example.com/dl-{}.jpg".format(post_id),
                headers={
                    "content-length": "512"
                }
            )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called()
        calls = [call(
            chat_id=update.message.chat_id,
            photo="http://example.com/dl-{}.jpg".format(post_id),
            caption="link-view/{}".format(post_id),
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
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id),
                    "link": "link-view/{}".format(post_id)
                },
                {
                    "id": post_id-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15),
                    "link": "link-view/{}".format(post_id-1)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "http://example.com/dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-view/{}".format(post_id)
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
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id),
                    "link": "link-view/{}".format(post_id)
                },
                {
                    "id": post_id-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15),
                    "link": "link-view/{}".format(post_id-1)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "http://example.com/dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_direct_link_and_different_submission_link(self, bot, r):
        username = "fender"
        image_id1 = 1560331512
        image_id2 = image_id1+300
        post_id1 = 232347
        post_id2 = 233447
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png https://furaffinity.net/view/{2}/".format(
                username, image_id1, post_id2
            )
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id2,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id2),
                    "link": "link-view/{}".format(post_id2)
                },
                {
                    "id": post_id1,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id1),
                    "link": "link-view/{}".format(post_id1)
                },
                {
                    "id": post_id1-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id1-15),
                    "link": "link-view/{}".format(post_id1-1)
                }
            ]
        )
        for post_id, image_id in [(post_id1, image_id1), (post_id2, image_id2)]:
            r.get(
                "{}/submission/{}.json".format(searchBot.api_url, post_id),
                json={
                    "full": "http://example.com/dl-{}.jpg".format(post_id),
                    "download": "http://example.com/dl-{}.jpg".format(post_id),
                    "link": "link-view/{}".format(post_id),
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
                }
            )
            r.head(
                "http://example.com/dl-{}.jpg".format(post_id),
                headers={
                    "content-length": "512"
                }
            )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called()
        calls = [call(
            chat_id=update.message.chat_id,
            photo="http://example.com/dl-{}.jpg".format(post_id),
            caption="link-view/{}".format(post_id),
            reply_to_message_id=update.message.message_id
        ) for post_id in [post_id1, post_id2]]
        bot.send_photo.assert_has_calls(calls)

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_submission_link_and_different_direct_link(self, bot, r):
        username = "fender"
        image_id1 = 1560331512
        image_id2 = image_id1+300
        post_id1 = 232347
        post_id2 = 233447
        update = MockTelegramUpdate.with_message(
            text="https://furaffinity.net/view/{2}/ http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(
                username, image_id1, post_id2
            )
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id2,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id2),
                    "link": "link-view/{}".format(post_id2)
                },
                {
                    "id": post_id1,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id1),
                    "link": "link-view/{}".format(post_id1)
                },
                {
                    "id": post_id1-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id1-15),
                    "link": "link-view/{}".format(post_id1-1)
                }
            ]
        )
        for post_id, image_id in [(post_id1, image_id1), (post_id2, image_id2)]:
            r.get(
                "{}/submission/{}.json".format(searchBot.api_url, post_id),
                json={
                    "full": "http://example.com/dl-{}.jpg".format(post_id),
                    "download": "http://example.com/dl-{}.jpg".format(post_id),
                    "link": "link-view/{}".format(post_id),
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
                }
            )
            r.head(
                "http://example.com/dl-{}.jpg".format(post_id),
                headers={
                    "content-length": "512"
                }
            )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called()
        calls = [call(
            chat_id=update.message.chat_id,
            photo="http://example.com/dl-{}.jpg".format(post_id),
            caption="link-view/{}".format(post_id),
            reply_to_message_id=update.message.message_id
        ) for post_id in [post_id2, post_id1]]
        bot.send_photo.assert_has_calls(calls)

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_result_on_first_page(self, bot, r):
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
                    "id": post_id+1,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16),
                    "link": "link-view/{}".format(post_id+1)
                },
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id),
                    "link": "link-view/{}".format(post_id)
                },
                {
                    "id": post_id-2,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-27),
                    "link": "link-view/{}".format(post_id-2)
                },
                {
                    "id": post_id-3,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-34),
                    "link": "link-view/{}".format(post_id-3)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "http://example.com/dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_result_on_third_page(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        for page in [1, 2, 3]:
            r.get(
                "{}/user/{}/gallery.json?page={}&full=1".format(searchBot.api_url, username, page),
                json=[
                    {
                        "id": post_id+1 + (3-page)*5,
                        "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16 + (3-page)*56),
                        "link": "link-view/{}".format(post_id+1 + (3-page)*5)
                    },
                    {
                        "id": post_id + (3-page)*5,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id + (3-page)*56),
                        "link": "link-view/{}".format(post_id + (3-page)*5)
                    },
                    {
                        "id": post_id-2 + (3-page)*5,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-27 + (3-page)*56),
                        "link": "link-view/{}".format(post_id-2 + (3-page)*5)
                    },
                    {
                        "id": post_id-3 + (3-page)*5,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-34 + (3-page)*56),
                        "link": "link-view/{}".format(post_id-3 + (3-page)*5)
                    }
                ]
            )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "http://example.com/dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_result_missing_from_first_page(self, bot, r):
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
                    "id": post_id+1,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16),
                    "link": "link-view/{}".format(post_id+1)
                },
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id+3),
                    "link": "link-view/{}".format(post_id)
                },
                {
                    "id": post_id-2,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-27),
                    "link": "link-view/{}".format(post_id-2)
                },
                {
                    "id": post_id-3,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-34),
                    "link": "link-view/{}".format(post_id-3)
                }
            ]
        )
        r.get(
            "{}/user/{}/scraps.json?page=1&full=1".format(searchBot.api_url, username),
            json=[]
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
    def test_result_missing_from_second_page(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        for page in [1, 2]:
            r.get(
                "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
                json=[
                    {
                        "id": post_id+1 + (2-page)*6,
                        "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16 + (2-page)*56),
                        "link": "link-view/{}".format(post_id+1 + (2-page)*6)
                    },
                    {
                        "id": post_id + (2-page)*6,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id+3 + (2-page)*56),
                        "link": "link-view/{}".format(post_id + (2-page)*6)
                    },
                    {
                        "id": post_id-2,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-27 + (2-page)*56),
                        "link": "link-view/{}".format(post_id-2)
                    },
                    {
                        "id": post_id-3,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-34 + (2-page)*56),
                        "link": "link-view/{}".format(post_id-3)
                    }
                ]
            )
        r.get(
            "{}/user/{}/scraps.json?page=1&full=1".format(searchBot.api_url, username),
            json=[]
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
    def test_result_missing_between_pages(self, bot, r):
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
                    "id": post_id+1,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16),
                    "link": "link-view/{}".format(post_id+1)
                },
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id+3),
                    "link": "link-view/{}".format(post_id)
                }
            ]
        )
        r.get(
            "{}/user/{}/gallery.json?page=2&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id-2,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-27),
                    "link": "link-view/{}".format(post_id-2)
                },
                {
                    "id": post_id-3,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-34),
                    "link": "link-view/{}".format(post_id-3)
                }
            ]
        )
        r.get(
            "{}/user/{}/scraps.json?page=1&full=1".format(searchBot.api_url, username),
            json=[]
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
    def test_result_last_on_page(self, bot, r):
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
                    "id": post_id+4,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16),
                    "link": "link-view/{}".format(post_id+4)
                },
                {
                    "id": post_id+3,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id+2),
                    "link": "link-view/{}".format(post_id+3)
                },
                {
                    "id": post_id+2,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id+1),
                    "link": "link-view/{}".format(post_id+2)
                },
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id),
                    "link": "link-view/{}".format(post_id)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "http://example.com/dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_result_first_on_page(self, bot, r):
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
                    "id": post_id+3,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16),
                    "link": "link-view/{}".format(post_id+3)
                },
                {
                    "id": post_id+2,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+8),
                    "link": "link-view/{}".format(post_id+2)
                }
            ]
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id),
                    "link": "link-view/{}".format(post_id)
                },
                {
                    "id": post_id-2,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-2),
                    "link": "link-view/{}".format(post_id-2)
                },
                {
                    "id": post_id-7,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-4),
                    "link": "link-view/{}".format(post_id-7)
                },
                {
                    "id": post_id-9,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-10),
                    "link": "link-view/{}".format(post_id-9)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "http://example.com/dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_not_on_first_page_empty_second_page(self, bot, r):
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
                    "id": post_id+3,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16)
                },
                {
                    "id": post_id+2,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+8)
                }
            ]
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[]
        )
        r.get(
            "{}/user/{}/scraps.json?page=1&full=1".format(searchBot.api_url, username),
            json=[]
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
    def test_result_in_scraps(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        for page in [1, 2]:
            r.get(
                "{}/user/{}/gallery.json?page={}&full=1".format(searchBot.api_url, username, page),
                json=[
                    {
                        "id": post_id+1 + (3-page)*5,
                        "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16 + (3-page)*56),
                        "link": "link-view/{}".format(post_id+1 + (3-page)*5)
                    },
                    {
                        "id": post_id + (3-page)*5,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id + (3-page)*56),
                        "link": "link-view/{}".format(post_id + (3-page)*5)
                    },
                    {
                        "id": post_id-2 + (3-page)*5,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-27 + (3-page)*56),
                        "link": "link-view/{}".format(post_id-2 + (3-page)*5)
                    },
                    {
                        "id": post_id-3 + (3-page)*5,
                        "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-34 + (3-page)*56),
                        "link": "link-view/{}".format(post_id-3 + (3-page)*5)
                    }
                ]
            )
        r.get(
            "{}/user/{}/gallery.json?page=3&full=1".format(searchBot.api_url, username),
            json=[]
        )
        r.get(
            "{}/user/{}/scraps.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id+1,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id+16),
                    "link": "link-view/{}".format(post_id+1)
                },
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id),
                    "link": "link-view/{}".format(post_id)
                },
                {
                    "id": post_id-2,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-27),
                    "link": "link-view/{}".format(post_id-2)
                },
                {
                    "id": post_id-3,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-34),
                    "link": "link-view/{}".format(post_id-3)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "http://example.com/dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
