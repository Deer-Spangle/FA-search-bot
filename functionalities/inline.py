import uuid
from typing import Tuple, List, Union, Optional

from telegram import InlineQueryResult, InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

from fa_export_api import FAExportAPI, PageNotFound
from functionalities.functionalities import BotFunctionality


class InlineFunctionality(BotFunctionality):

    def __init__(self, api: FAExportAPI):
        super().__init__(InlineQueryHandler)
        self.api = api

    def call(self, bot, update):
        query = update.inline_query.query
        query_clean = query.strip().lower()
        offset = update.inline_query.offset
        print(f"Got an inline query: {query}, page={offset}")
        if query_clean == "":
            bot.answer_inline_query(update.inline_query.id, [])
            return
        # Get results and next offset
        if any(query_clean.startswith(x) for x in ["favourites:", "favs:", "favorites:"]):
            _, username = query_clean.split(":", 1)
            results, next_offset = self._favs_query_results(username, offset)
        else:
            gallery_query = self._parse_folder_and_username(query_clean)
            if gallery_query:
                folder, username = gallery_query
                results, next_offset = self._gallery_query_results(folder, username, offset)
            else:
                results, next_offset = self._search_query_results(query, offset)
        # Send results
        bot.answer_inline_query(update.inline_query.id, results, next_offset=next_offset)

    def _favs_query_results(self, username: str, offset: str) -> Tuple[List[InlineQueryResult], Union[int, str]]:
        if offset == "":
            offset = None
        try:
            submissions = self.api.get_user_favs(username, offset)[:48]
        except PageNotFound:
            return self._user_not_found(username), ""
        # If no results, send error
        if len(submissions) > 0:
            next_offset = submissions[-1].fav_id
            if next_offset == offset:
                submissions = []
                next_offset = ""
        else:
            next_offset = ""
            if offset is None:
                return self._empty_user_favs(username), ""
        results = [x.to_inline_query_result() for x in submissions]
        return results, next_offset

    def _gallery_query_results(self, folder: str, username: str, offset: str) \
            -> Tuple[List[InlineQueryResult], Union[int, str]]:
        # Parse offset to page and skip
        if offset == "":
            page, skip = 1, None
        elif ":" in offset:
            page, skip = (int(x) for x in offset.split(":", 1))
        else:
            page, skip = int(offset), None
        # Default next offset
        next_offset = page + 1
        # Try and get results
        try:
            results = self._create_user_folder_results(username, folder, page)
        except PageNotFound:
            return self._user_not_found(username), ""
        # If no results, send error
        if len(results) == 0:
            next_offset = ""
            if page == 1:
                return self._empty_user_folder(username, folder), ""
        # Handle paging of big result lists
        if skip:
            results = results[skip:]
        if len(results) > 48:
            results = results[:48]
            if skip:
                skip += 48
            else:
                skip = 48
            next_offset = f"{page}:{skip}"
        return results, next_offset

    def _search_query_results(self, query: str, offset: str) -> Tuple[List[InlineQueryResult], Union[int, str]]:
        page = self._page_from_offset(offset)
        query_clean = query.strip().lower()
        next_offset = page + 1
        results = self._create_inline_search_results(query_clean, page)
        if len(results) == 0:
            next_offset = ""
            if page == 1:
                results = self._no_search_results_found(query)
        return results, next_offset

    def _page_from_offset(self, offset: str) -> int:
        if offset == "":
            offset = 1
        return int(offset)

    def _create_user_folder_results(self, username: str, folder: str, page: int) -> List[InlineQueryResultPhoto]:
        return [
            x.to_inline_query_result()
            for x
            in self.api.get_user_folder(username, folder, page)
        ]

    def _create_inline_search_results(self, query_clean: str, page: int) -> List[InlineQueryResultPhoto]:
        return [
            x.to_inline_query_result()
            for x
            in self.api.get_search_results(query_clean, page)
        ]

    def _parse_folder_and_username(self, query_clean: str) -> Optional[Tuple[str, str]]:
        if query_clean.startswith("gallery:") or query_clean.startswith("scraps:"):
            folder, username = query_clean.split(":", 1)
            return folder, username
        else:
            return None

    def _empty_user_folder(self, username: str, folder: str) -> List[InlineQueryResultArticle]:
        return [
            InlineQueryResultArticle(
                id=uuid.uuid4(),
                title=f"Nothing in {folder}.",
                input_message_content=InputTextMessageContent(
                    message_text=f"There are no submissions in {folder} for user \"{username}\"."
                )
            )
        ]

    def _empty_user_favs(self, username: str) -> List[InlineQueryResultArticle]:
        return [
            InlineQueryResultArticle(
                id=uuid.uuid4(),
                title=f"Nothing in favourites.",
                input_message_content=InputTextMessageContent(
                    message_text=f"There are no favourites for user \"{username}\"."
                )
            )
        ]

    def _no_search_results_found(self, query: str) -> List[InlineQueryResultArticle]:
        return [
            InlineQueryResultArticle(
                id=uuid.uuid4(),
                title="No results found.",
                input_message_content=InputTextMessageContent(
                    message_text=f"No results for search \"{query}\"."
                )
            )
        ]

    def _user_not_found(self, username: str) -> List[InlineQueryResultArticle]:
        return [
            InlineQueryResultArticle(
                id=uuid.uuid4(),
                title="User does not exist.",
                input_message_content=InputTextMessageContent(
                    message_text=f"FurAffinity user does not exist by the name: \"{username}\"."
                )
            )
        ]