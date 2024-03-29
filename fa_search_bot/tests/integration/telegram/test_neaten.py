from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import requests

if TYPE_CHECKING:
    from pyrogram.types import Chat
    from tgintegration import BotController

    from fa_search_bot.bot import FASearchBot


pytestmark = pytest.mark.asyncio


async def test_neaten_link(controller: BotController):
    # - send link, get neatened pic
    async with controller.collect(count=2) as response:
        await controller.client.send_message(controller.peer_id, "https://www.furaffinity.net/view/19925704/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "19925704" in response.messages[-1].caption
    assert response.messages[-1].photo


async def test_neaten_link_in_group(controller: BotController, group_chat: Chat):
    # - neaten link in group
    group_id = group_chat.id
    async with controller.collect(count=2, peer=group_id) as response:
        await controller.client.send_message(group_id, "https://www.furaffinity.net/view/19925704/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "19925704" in response.messages[-1].caption
    assert response.messages[-1].photo


async def test_no_neaten_caption_in_group(controller: BotController, group_chat: Chat):
    # - in group neaten doesn't reply to image with caption link
    group_id = group_chat.id
    thumb_link = "https://t.furaffinity.net/19925704@400-1462827244.jpg"
    async with controller.collect(peer=group_id, raise_=False) as response:
        await controller.client.send_photo(group_id, thumb_link, caption="https://www.furaffinity.net/view/19925704/")

    assert response.num_messages == 0


async def test_neaten_link_in_button(controller: BotController, bot: FASearchBot):
    # Creating an example message to forward to the bot
    client_user = await controller.client.get_me()
    user_id = client_user.id
    async with controller.collect(count=1) as test_msg:
        requests.post(
            f"https://api.telegram.org/bot{bot.bot_key}/sendMessage",
            json={
                "chat_id": user_id,
                "text": "Hello there",
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {
                                "text": "View on FA",
                                "url": "https://www.furaffinity.net/view/19925704/",
                            }
                        ]
                    ]
                },
            },
        )
    msg_id = test_msg.messages[0].message_id

    # Run the test
    async with controller.collect(count=2) as response:
        await controller.client.forward_messages(controller.peer_id, controller.peer_id, msg_id)

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "19925704" in response.messages[-1].caption
    assert response.messages[-1].photo


async def test_neaten_link_in_button_with_image(controller: BotController, bot: FASearchBot):
    # Creating an example message to forward to the bot
    client_user = await controller.client.get_me()
    user_id = client_user.id
    async with controller.collect(count=1) as test_msg:
        requests.post(
            f"https://api.telegram.org/bot{bot.bot_key}/sendPhoto",
            json={
                "chat_id": user_id,
                "photo": "https://t.furaffinity.net/19925704@400-1462827244.jpg",
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {
                                "text": "View on FA",
                                "url": "https://www.furaffinity.net/view/19925704/",
                            }
                        ]
                    ]
                },
            },
        )
    msg_id = test_msg.messages[0].message_id

    # Run the test
    async with controller.collect(count=2) as response:
        await controller.client.forward_messages(controller.peer_id, controller.peer_id, msg_id)

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "19925704" in response.messages[-1].caption
    assert response.messages[-1].photo


async def test_neaten_txt_link(controller: BotController):
    # - send link, get neatened pic
    async with controller.collect(count=2) as response:
        await controller.client.send_message(controller.peer_id, "https://www.furaffinity.net/view/572932/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "572932" in response.messages[-1].caption
    assert "Kandrel" in response.messages[-1].caption
    assert "Lunch Break" in response.messages[-1].caption
    assert response.messages[-1].photo


async def test_neaten_pdf_link(controller: BotController):
    # - send link, get neatened pic
    async with controller.collect(count=2) as response:
        await controller.client.send_message(controller.peer_id, "https://www.furaffinity.net/view/41734655/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "41734655" in response.messages[-1].caption
    assert "Jaystoat" in response.messages[-1].caption
    assert "Lights In The Sky" in response.messages[-1].caption
    assert response.messages[-1].document


async def test_neaten_e621_link(controller: BotController):
    # - send link, get neatened pic
    async with controller.collect(count=2) as response:
        await controller.client.send_message(controller.peer_id, "https://e621.net/posts/1092773/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "1092773" in response.messages[-1].caption
    assert response.messages[-1].photo


async def test_neaten_audio_link(controller: BotController):
    # - Send audio link, get neatened audio
    async with controller.collect(count=2) as response:
        await controller.client.send_message(controller.peer_id, "https://furaffinity.net/view/51778891/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "51778891" in response.messages[-1].caption
    assert response.messages[-1].audio
    assert "Rosemary" in response.messages[-1].audio.title
    assert "xSini" in response.messages[-1].audio.performer


async def test_neaten_static_gif_link(controller: BotController):
    # - send link to static gif, get neatened pic (not animation)
    async with controller.collect(count=2) as response:
        await controller.client.send_message(controller.peer_id, "https://furaffinity.net/view/27575057/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "27575057" in response.messages[-1].caption
    assert response.messages[-1].photo
