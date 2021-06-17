import os

import pytest
from tgintegration import BotController

from fa_search_bot.bot import FASearchBot
from fa_search_bot.sites.fa_submission import FASubmission

pytestmark = pytest.mark.asyncio


async def test_neaten_gif(controller: BotController):
    # - send link, make pretty gif
    submission_id = "27408045"
    # Delete cache
    filename = f"{FASubmission.GIF_CACHE_DIR}/{submission_id}.mp4"
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
    filename = submission._get_video_from_cache()
    if filename is None:
        output_path = await submission._convert_gif(submission.download_url)
        submission._save_video_to_cache(output_path)

    async with controller.collect(count=2) as response:
        await controller.client.send_message(controller.peer_id, "https://www.furaffinity.net/view/27408045/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert submission_id in response.messages[-1].caption
    assert response.messages[-1].animation
