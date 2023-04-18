from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from fa_search_bot.database import Database
from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.submission_cache import SubmissionCache

if TYPE_CHECKING:
    from tgintegration import BotController

    from fa_search_bot.bot import FASearchBot

pytestmark = pytest.mark.asyncio


async def test_neaten_gif(controller: BotController):
    # - send link, make pretty gif
    site_code = "fa"
    submission_id = "27408045"
    # Delete cache
    db = Database()
    db._just_execute("DELETE FROM cache_entries WHERE site_code = ? AND submission_id = ?", (site_code, submission_id))

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
    site_code = "fa"
    submission_id = "27408045"
    # Populate cache
    db = Database()
    cache = SubmissionCache(db)
    cache_entry = cache.load_cache(SubmissionID(site_code, submission_id))
    if cache_entry is None:
        submission = await bot.api.get_full_submission(submission_id)
        sendable = SendableFASubmission(submission)
        client_user = await controller.client.get_me()
        user_id = client_user.id
        sent_sub = await sendable.send_message(bot.client, user_id)
        cache.save_cache(sent_sub)

    async with controller.collect(count=2, max_wait=300) as response:
        await controller.client.send_message(controller.peer_id, "https://www.furaffinity.net/view/27408045/")

    # TODO: check convert wasn't called
    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert submission_id in response.messages[-1].caption
    assert response.messages[-1].animation


@pytest.mark.asyncio
async def test_neaten_webm(controller: BotController):
    # - send link, make video from webm
    site_code = "e6"
    post_id = "2379470"
    # Delete cache
    db = Database()
    db._just_execute("DELETE FROM cache_entries WHERE site_code = ? AND submission_id = ?", (site_code, post_id))

    # Send neaten command
    async with controller.collect(count=2, max_wait=600) as response:
        await controller.client.send_message(controller.peer_id, f"https://e621.net/posts/{post_id}/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert post_id in response.messages[-1].caption
    assert response.messages[-1].video
