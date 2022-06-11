import os
from typing import TYPE_CHECKING

import pytest

from fa_search_bot.sites.fa_handler import SendableFASubmission
from fa_search_bot.sites.sendable import Sendable

if TYPE_CHECKING:
    from tgintegration import BotController

    from fa_search_bot.bot import FASearchBot

pytestmark = pytest.mark.asyncio


async def test_neaten_gif(controller: BotController):
    # - send link, make pretty gif
    submission_id = "27408045"
    # Delete cache
    filename = f"{Sendable.CACHE_DIR}/fa/{submission_id}.mp4"
    if os.path.exists(filename):
        os.remove(filename)

    # Send neaten command
    async with controller.collect(count=2, max_wait=300) as response:
        await controller.client.send_message(controller.peer_id, f"https://www.furaffinity.net/view/{submission_id}/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert submission_id in response.messages[-1].caption
    assert response.messages[-1].animation


@pytest.mark.asyncio
async def test_neaten_gif_from_cache(controller: BotController, bot: FASearchBot):
    # - send link, get pretty gif from cache
    submission_id = "27408045"
    # Populate cache
    submission = await bot.api.get_full_submission(submission_id)
    sendable = SendableFASubmission(submission)
    filename = sendable._get_video_from_cache()
    if filename is None:
        output_path = await sendable._convert_gif(submission.download_url)
        sendable._save_video_to_cache(output_path)

    async with controller.collect(count=2, max_wait=300) as response:
        await controller.client.send_message(controller.peer_id, "https://www.furaffinity.net/view/27408045/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert submission_id in response.messages[-1].caption
    assert response.messages[-1].animation


@pytest.mark.asyncio
async def test_neaten_webm(controller: BotController):
    # - send link, make video from webm
    post_id = "2379470"
    # Delete cache
    filename = f"{Sendable.CACHE_DIR}/e6/{post_id}.mp4"
    if os.path.exists(filename):
        os.remove(filename)

    # Send neaten command
    async with controller.collect(count=2, max_wait=600) as response:
        await controller.client.send_message(controller.peer_id, f"https://e621.net/posts/{post_id}/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert post_id in response.messages[-1].caption
    assert response.messages[-1].video
