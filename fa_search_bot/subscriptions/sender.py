from __future__ import annotations

import collections
import datetime
import logging
from typing import Union, Dict, List

import heartbeat
from prometheus_client import Counter
from telethon.errors import UserIsBlockedError, InputUserDeactivatedError, ChannelPrivateError, PeerIdInvalidError
from telethon.tl.types import TypeInputPeer

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.subscriptions.runnable import Runnable
from fa_search_bot.subscriptions.subscription import Subscription
from fa_search_bot.subscriptions.utils import time_taken
from fa_search_bot.subscriptions.wait_pool import SubmissionCheckState

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
            # Send out messages
            with time_taken_sending_messages.time():
                await self._send_updates(next_state)
            sent_count += 1
            # Update latest ids with the submission we just checked, and save config
            with time_taken_saving_config.time():
                self.watcher.update_latest_id(next_state.sub_id)
            # If we've done ten, update heartbeat
            if sent_count % self.UPDATE_PER_HEARTBEAT == 0:
                with time_taken_updating_heartbeat.time():
                    heartbeat.update_heartbeat(heartbeat_app_name)
                logger.debug("Heartbeat")

    async def _send_updates(self, state: SubmissionCheckState) -> None:
        subscriptions = state.matching_subscriptions
        sendable = SendableFASubmission(state.full_data)
        # Map which subscriptions require this submission at each destination
        destination_map: Dict[int, List[Subscription]] = collections.defaultdict(lambda: [])
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
                await self._send_subscription_update(sendable, state, dest, prefix)
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
        state: SubmissionCheckState,
        chat: Union[int, TypeInputPeer],
        prefix: str,
    ) -> None:
        if state.cache_entry:
            if await state.cache_entry.try_to_send(self.watcher.client, chat, prefix=prefix):
                return
            # TODO: Need to re-upload, instrument that
        # Send message. (If uploaded media isn't set, it'll re-upload
        result = await sendable.send_message(
            self.watcher.client,
            chat,
            prefix=prefix,
            uploaded_media=state.uploaded_media
        )
        self.watcher.submission_cache.save_cache(result)
        return result