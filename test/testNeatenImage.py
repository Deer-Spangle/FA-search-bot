import unittest

from unittest.mock import patch, call

import requests_mock
import telegram
from telegram import Chat

from bot import FASearchBot
from fa_submission import FASubmission
from test.util.testTelegramUpdateObjects import MockTelegramUpdate

searchBot = FASearchBot("config-test.json")


class NeatenImageTest(unittest.TestCase):

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
    def test_submission_link(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
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
    def test_submission_group_chat(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.GROUP
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
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
    def test_submission_link_no_http(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="furaffinity.net/view/{}".format(post_id))
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
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
    def test_two_submission_links(self, bot, r):
        id1 = 23636984
        id2 = 23636996
        update = MockTelegramUpdate.with_message(
            text="furaffinity.net/view/{}\nfuraffinity.net/view/{}".format(id1, id2)
        )
        for post_id in [id1, id2]:
            r.get(
                "{}/submission/{}.json".format(searchBot.api_url, post_id),
                json={
                    "full": "http://example.com/dl-{}.jpg".format(post_id),
                    "download": "http://example.com/dl-{}.jpg".format(post_id),
                    "link": "link-view/{}".format(post_id),
                    "thumbnail": "http://url.com/thumb@400-1223432.jpg"
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
        ) for post_id in [id1, id2]]
        bot.send_photo.assert_has_calls(calls)

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_duplicate_submission_links(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="furaffinity.net/view/{0}\nfuraffinity.net/view/{0}".format(post_id)
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
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
    def test_deleted_submission(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="furaffinity.net/view/{}".format(post_id))
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            status_code=404,
            json={
                "error": "error",
                "url": "link-view/{}".format(post_id)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_called_once()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert "This doesn't seem to be a valid FA submission" in bot.send_message.call_args[1]['text']
        assert str(post_id) in bot.send_message.call_args[1]['text']
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_deleted_submission_group_chat(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="furaffinity.net/view/{}".format(post_id), chat_type=Chat.GROUP)
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            status_code=404,
            json={
                "error": "error",
                "url": "link-view/{}".format(post_id)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_not_called()

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_gif_submission(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/dl-{}.gif".format(post_id),
                "download": "http://example.com/dl-{}.gif".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
            }
        )
        r.head(
            "http://example.com/dl-{}.gif".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_document.call_args[1]['document'] == "http://example.com/dl-{}.gif".format(post_id)
        assert bot.send_document.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_document.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_pdf_submission(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "http://example.com/full-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.pdf".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
            }
        )
        r.head(
            "http://example.com/dl-{}.pdf".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_document.call_args[1]['document'] == "http://example.com/dl-{}.pdf".format(post_id)
        assert bot.send_document.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_document.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_mp3_submission(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.mp3".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
            }
        )
        r.head(
            "http://example.com/dl-{}.mp3".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()
        bot.send_audio.assert_called_once()
        assert bot.send_audio.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_audio.call_args[1]['audio'] == "http://example.com/dl-{}.mp3".format(post_id)
        assert bot.send_audio.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_audio.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_txt_submission(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.txt".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_called_once()
        bot.send_document.assert_not_called()
        bot.send_audio.assert_not_called()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "thumb-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == \
            "link-view/{0}\n[Direct download](http://example.com/dl-{0}.txt)".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_swf_submission(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.PRIVATE
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.swf".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
            }
        )
        r.head(
            "http://example.com/dl-{}.swf".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_called_once()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "I'm sorry, I can't neaten \".swf\" files."
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_swf_submission_groupchat(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.GROUP
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.swf".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
            }
        )
        r.head(
            "http://example.com/dl-{}.swf".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_unknown_type_submission(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.PRIVATE
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.zzz".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
            }
        )
        r.head(
            "http://example.com/dl-{}.zzz".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_called_once()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "I'm sorry, I don't understand that file extension (zzz)."
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_unknown_type_submission_groupchat(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.GROUP
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.zzz".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
            }
        )
        r.head(
            "http://example.com/dl-{}.zzz".format(post_id),
            headers={
                "content-length": "512"
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_link_in_markdown(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="[Hello](https://www.furaffinity.net/view/{}/)".format(post_id)
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "http://url.com/thumb@400-1223432.jpg"
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
    def test_image_just_under_size_limit(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "thumb-{}.jpg".format(post_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": str(FASubmission.SIZE_LIMIT_IMAGE - 1)
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
    def test_image_just_over_size_limit(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "thumb-{}.jpg".format(post_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": str(FASubmission.SIZE_LIMIT_IMAGE + 1)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "thumb-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == \
            "link-view/{0}\n[Direct download](http://example.com/dl-{0}.jpg)".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_image_over_document_size_limit(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.jpg".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "thumb-{}.jpg".format(post_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.jpg".format(post_id),
            headers={
                "content-length": str(FASubmission.SIZE_LIMIT_DOCUMENT + 1)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "thumb-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == \
            "link-view/{0}\n[Direct download](http://example.com/dl-{0}.jpg)".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_auto_doc_just_under_size_limit(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.gif".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "thumb-{}.jpg".format(post_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.gif".format(post_id),
            headers={
                "content-length": str(FASubmission.SIZE_LIMIT_DOCUMENT - 1)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_document.assert_called_once()
        bot.send_photo.assert_not_called()
        bot.send_message.assert_not_called()
        assert bot.send_document.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_document.call_args[1]['document'] == "http://example.com/dl-{}.gif".format(post_id)
        assert bot.send_document.call_args[1]['caption'] == "link-view/{}".format(post_id)
        assert bot.send_document.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_auto_doc_just_over_size_limit(self, bot, r):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, post_id),
            json={
                "full": "thumb-{}.jpg".format(post_id),
                "download": "http://example.com/dl-{}.pdf".format(post_id),
                "link": "link-view/{}".format(post_id),
                "thumbnail": "thumb-{}.jpg".format(post_id)
            }
        )
        r.head(
            "http://example.com/dl-{}.pdf".format(post_id),
            headers={
                "content-length": str(FASubmission.SIZE_LIMIT_DOCUMENT + 1)
            }
        )

        searchBot.neaten_image(bot, update)

        bot.send_photo.assert_called_once()
        bot.send_document.assert_not_called()
        bot.send_message.assert_not_called()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "thumb-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == \
            "link-view/{0}\n[Direct download](http://example.com/dl-{0}.pdf)".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN
