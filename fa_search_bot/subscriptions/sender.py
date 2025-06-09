from __future__ import annotations

import asyncio
import collections
import datetime
import logging
from typing import Union, Dict, List, Optional, TYPE_CHECKING

from prometheus_client import Counter
from telethon.errors import UserIsBlockedError, InputUserDeactivatedError, ChannelPrivateError, PeerIdInvalidError, FloodWaitError
from telethon.errors.rpcerrorlist import FilePartMissingError, FilePart0MissingError
from telethon.tl.types import TypeInputPeer

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.subscriptions.runnable import Runnable
from fa_search_bot.subscriptions.subscription import Subscription
from fa_search_bot.subscriptions.utils import time_taken
from fa_search_bot.subscriptions.wait_pool import SubmissionCheckState

if TYPE_CHECKING:
    from fa_search_bot.subscriptions.subscription_watcher import SubscriptionWatcher


logger = logging.getLogger(__name__)

time_taken_reading_queue = time_taken.labels(task="reading wait-pool for new data", runnable="Sender")
time_taken_waiting = time_taken.labels(task="waiting for new events in queue", runnable="Sender")
time_taken_sending_messages = time_taken.labels(task="sending messages to subscriptions", runnable="Sender")
time_taken_saving_config = time_taken.labels(task="updating configuration", runnable="Sender")
sub_updates = Counter("fasearchbot_subscriptionsender_updates_sent_total", "Number of subscription updates sent")
sub_blocked = Counter(
    "fasearchbot_subscriptionsender_dest_blocked_total",
    "Number of times a destination has turned out to have blocked or deleted the bot without pausing subs first",
)
sub_update_send_failures = Counter(
    "fasearchbot_subscriptionsender_updates_failed_total",
    "Number of subscription updates which failed for unknown reason",
)
total_updates_sent = Counter(
    "fasearchbot_subscriptionsender_messages_sent",
    "Number of messages sent by the subscription sender",
    labelnames=["media_type"],
)
updates_sent_cache = total_updates_sent.labels(media_type="cached")
updates_sent_fresh_cache = total_updates_sent.labels(media_type="fresh_cache")
updates_sent_upload = total_updates_sent.labels(media_type="upload")
updates_sent_re_upload = total_updates_sent.labels(media_type="re_upload")


class Sender(Runnable):
    WAIT_BETWEEN_FLOOD_LOGS = datetime.timedelta(60)
    SEND_ATTEMPTS = 3

    def __init__(self, watcher: "SubscriptionWatcher") -> None:
        super().__init__(watcher)
        self.last_state: Optional[SubmissionCheckState] = None

    async def do_process(self) -> None:
        with time_taken_reading_queue.time():
            next_state = await self.watcher.wait_pool.pop_next_ready_to_send()
        if not next_state:
            with time_taken_waiting.time():
                await asyncio.sleep(self.QUEUE_BACKOFF)
            return
        self.last_state = next_state
        logger.debug("Got submission ready to send: %s", next_state.sub_id)
        # Send out messages
        with time_taken_sending_messages.time():
            await self._send_updates(next_state)
        logger.debug("Sent messages for submission %s", next_state.sub_id)
        # Log the posting date of the latest sent submission
        self.watcher.update_latest_observed(next_state.full_data.posted_at)
        # Update latest ids with the submission we just checked, and save config
        with time_taken_saving_config.time():
            self.watcher.update_latest_id(next_state.sub_id)

    async def _send_updates(self, state: SubmissionCheckState) -> None:
        sendable = SendableFASubmission(state.full_data)
        # Get subscriptions list again, because it might have changed since DataFetcher checked
        subscriptions = self.watcher.check_subscriptions(state.full_data)
        # Map which subscriptions require this submission at each destination
        destination_map: Dict[int, List[Subscription]] = collections.defaultdict(lambda: [])
        for sub in subscriptions:
            sub.latest_update = datetime.datetime.now()
            destination_map[sub.destination].append(sub)
        # Send the submission to each location
        for dest, subs in destination_map.items():
            if dest in state.sent_to:
                # Already sent to that destination, skip
                continue
            queries = ", ".join([f'"{sub.query_str}"' for sub in subs])
            prefix = f"Update on {queries} subscription{'' if len(subs) == 1 else 's'}:"
            await self._try_send_subscription_update(sendable, state, dest, prefix)

    async def _try_send_subscription_update(
        self,
        sendable: SendableFASubmission,
        state: SubmissionCheckState,
        chat: Union[int, TypeInputPeer],
        prefix: str,
    ) -> None:
        send_attempt = 0
        while send_attempt < self.SEND_ATTEMPTS:
            send_attempt += 1
            logger.info("Sending submission %s to subscription", sendable.submission_id)
            sub_updates.inc()
            try:
                await self._send_subscription_update(sendable, state, chat, prefix)
                state.sent_to.append(chat)
                return
            except (UserIsBlockedError, InputUserDeactivatedError, ChannelPrivateError, PeerIdInvalidError):
                sub_blocked.inc()
                logger.info("Destination %s is blocked or deleted, pausing subscriptions", chat)
                all_subs = [sub for sub in self.watcher.subscriptions if sub.destination == chat]
                for sub in all_subs:
                    sub.paused = True
                return
            except FloodWaitError as e:
                seconds = e.seconds
                logger.warning("Received flood wait error, have to sleep %s seconds", seconds)
                await self._flood_wait(seconds)
                logger.info("Flood wait complete, retrying sending submission")
                continue
            except (FilePartMissingError, FilePart0MissingError) as e:
                logger.warning(
                    "Received file part missing error for submission %s, will reset cache and re-attempt",
                    sendable.submission_id,
                )
                state.uploaded_media = None
                state.cache_entry = None
                state.full_data = None
                self.watcher.wait_pool.return_populated_state(state)
                await self.watcher.fetch_data_queue.put_refresh(sendable.submission_id)
                continue
            except Exception as e:
                sub_update_send_failures.inc()
                logger.error(
                    "Failed to send submission: %s to %s",
                    sendable.submission_id,
                    chat,
                    exc_info=e,
                )
                raise e

    async def _send_subscription_update(
        self,
        sendable: SendableFASubmission,
        state: SubmissionCheckState,
        chat: Union[int, TypeInputPeer],
        prefix: str,
    ) -> None:
        # If this has previously been sent, send again
        if state.cache_entry:
            if await state.cache_entry.try_to_send(self.watcher.client, chat, prefix=prefix):
                updates_sent_cache.inc()
                return
        # If uploaded media isn't set, check cache again
        if not state.uploaded_media:
            cache_entry = self.watcher.submission_cache.load_cache(state.sub_id)
            if cache_entry:
                if await cache_entry.try_to_send(self.watcher.client, chat, prefix=prefix):
                    updates_sent_fresh_cache.inc()
                    await self.watcher.wait_pool.set_cached(state.sub_id, cache_entry)
                    return
            updates_sent_re_upload.inc()
        else:
            updates_sent_upload.inc()
        # Send message
        result = await sendable.send_message(
            self.watcher.client,
            chat,
            prefix=prefix,
            uploaded_media=state.uploaded_media
        )
        logger.info("Sent submission %s to %s", state.sub_id, chat)
        self.watcher.submission_cache.save_cache(result)
        return result

    async def revert_last_attempt(self) -> None:
        """
        As there's only 1 Sender, we can push the state back into the wait pool if it failed.
        If there were more than 1 Sender, this would risk posts being out of order, as the other would have grabbed a
        new post to send. But having more than 1 Sender would present multiple other challenges.
        """
        if self.last_state is None:
            raise ValueError("Can't revert last attempt, as last attempt did not exist")
        self.watcher.wait_pool.return_populated_state(self.last_state)

    async def _flood_wait(self, seconds: int) -> None:
        start_time = datetime.datetime.now(tz=datetime.timezone.utc)
        end_time = start_time + datetime.timedelta(seconds=seconds)
        remaining_time = end_time - datetime.datetime.now(tz=datetime.timezone.utc)
        while remaining_time > datetime.timedelta(seconds=0):
            logger.warning("Waiting for flood warning to expire. %s seconds remain", remaining_time.total_seconds())
            sleep_batch = min(remaining_time, self.WAIT_BETWEEN_FLOOD_LOGS)
            await self._wait_while_running(sleep_batch.total_seconds())
            remaining_time = end_time - datetime.datetime.now(tz=datetime.timezone.utc)
        logger.info("Flood wait complete")
