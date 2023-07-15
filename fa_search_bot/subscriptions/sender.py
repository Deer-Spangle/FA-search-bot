from __future__ import annotations

import collections
import datetime
import logging
from typing import List

import heartbeat
from prometheus_client import Counter
from telethon.errors import UserIsBlockedError, InputUserDeactivatedError, ChannelPrivateError, PeerIdInvalidError
from telethon.tl.types import TypeInputPeer

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.sites.sendable import UploadedMedia
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.subscriptions.runnable import Runnable
from fa_search_bot.subscriptions.subscription import Subscription
from fa_search_bot.subscriptions.utils import time_taken

logger = logging.getLogger(__name__)

heartbeat.heartbeat_app_url = "https://heartbeat.spangle.org.uk/"
heartbeat_app_name = "FASearchBot_sub_thread"

time_taken_sending_messages = time_taken.labels(task="sending messages to subscriptions")
time_taken_saving_config = time_taken.labels(task="updating configuration")
time_taken_updating_heartbeat = time_taken.labels(task="updating heartbeat")
sub_updates = Counter("fasearchbot_fasubwatcher_updates_sent_total", "Number of subscription updates sent")
sub_blocked = Counter(
    "fasearchbot_fasubwatcher_dest_blocked_total",
    "Number of times a destination has turned out to have blocked or deleted the bot without pausing subs first",
)
sub_update_send_failures = Counter(
    "fasearchbot_fasubwatcher_updates_failed_total",
    "Number of subscription updates which failed for unknown reason",
)


class Sender(Runnable):
    UPDATE_PER_HEARTBEAT = 10

    async def run(self) -> None:
        sent_count = 0
        while self.running:
            next_state = await self.watcher.wait_pool.pop_next_ready_to_send()
            # TODO: handle cache entries
            with time_taken_sending_messages.time():
                await self._send_updates(
                    next_state.matching_subscriptions,
                    SendableFASubmission(next_state.full_data),
                    next_state.uploaded_media,
                )
            sent_count += 1
            # Update latest ids with the submission we just checked, and save config
            with time_taken_saving_config.time():
                self.watcher.update_latest_id(next_state.sub_id)
            # If we've done ten, update heartbeat
            if sent_count % self.UPDATE_PER_HEARTBEAT == 0:
                with time_taken_updating_heartbeat.time():
                    heartbeat.update_heartbeat(heartbeat_app_name)
                logger.debug("Heartbeat")

    async def _send_updates(
            self,
            subscriptions: List["Subscription"],
            sendable: SendableFASubmission,
            uploaded_media: UploadedMedia,
    ) -> None:
        # Map which subscriptions require this submission at each destination
        destination_map = collections.defaultdict(lambda: [])
        for sub in subscriptions:
            sub.latest_update = datetime.datetime.now()
            destination_map[sub.destination].append(sub)
        # Send the submission to each location
        for dest, subs in destination_map.items():
            queries = ", ".join([f'"{sub.query_str}"' for sub in subs])
            prefix = f"Update on {queries} subscription{'' if len(subs) == 1 else 's'}:"
            logger.info("Sending submission %s to subscription", sendable.submission_id)
            sub_updates.inc()
            try:
                await self._send_subscription_update(sendable, uploaded_media, dest, prefix)
            except (UserIsBlockedError, InputUserDeactivatedError, ChannelPrivateError, PeerIdInvalidError):
                sub_blocked.inc()
                logger.info("Destination %s is blocked or deleted, pausing subscriptions", dest)
                all_subs = [sub for sub in self.watcher.subscriptions if sub.destination == dest]
                for sub in all_subs:
                    sub.paused = True
            except Exception as e:
                sub_update_send_failures.inc()
                logger.error(
                    "Failed to send submission: %s to %s",
                    sendable.submission_id,
                    dest,
                    exc_info=e,
                )

    async def _send_subscription_update(
        self,
        sendable: SendableFASubmission,
        uploaded: UploadedMedia,
        chat: TypeInputPeer,
        prefix: str,
    ) -> SentSubmission:
        cache_entry = self.watcher.submission_cache.load_cache(sendable.submission_id)
        if cache_entry:
            if await cache_entry.try_to_send(self.watcher.client, chat, prefix=prefix):
                return cache_entry
        result = await sendable.send_message(self.watcher.client, chat, prefix=prefix, uploaded_media=uploaded)
        self.watcher.submission_cache.save_cache(result)
        return result
