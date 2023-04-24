from __future__ import annotations
import dataclasses
import datetime
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Optional, Union, Tuple, Dict, ContextManager, TYPE_CHECKING

import dateutil.parser

if TYPE_CHECKING:
    from sqlite3 import Cursor


@dataclasses.dataclass
class DBCacheEntry:
    site_code: str
    submission_id: str
    is_photo: bool
    media_id: int
    access_hash: int
    file_url: Optional[str]
    caption: str
    cache_date: datetime.datetime
    full_image: bool


class Database:
    DB_FILE = "fasearchbot_db.sqlite"

    def __init__(self) -> None:
        self.conn = sqlite3.connect(self.DB_FILE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = RLock()
        self._create_db()

    def _create_db(self) -> None:
        cur = self.conn.cursor()
        directory = Path(__file__).parent
        with open(directory / "database_schema.sql", "r") as f:
            cur.executescript(f.read())
        self.conn.commit()

    @contextmanager
    def _execute(self, query: str, args: Optional[Union[Tuple, Dict]] = None) -> ContextManager[Cursor]:
        with self._lock:
            cur = self.conn.cursor()
            try:
                if args:
                    result = cur.execute(query, args)
                else:
                    result = cur.execute(query)
                self.conn.commit()
                yield result
            finally:
                cur.close()

    def _just_execute(self, query: str, args: Optional[Union[Tuple, Dict]] = None) -> None:
        with self._execute(query, args):
            pass

    def fetch_cache_entry(self, site_code: str, submission_id: str) -> Optional[DBCacheEntry]:
        with self._execute(
                "SELECT is_photo, media_id, access_hash, file_url, caption, cache_date, full_image "
                "FROM cache_entries WHERE site_code = ? AND submission_id = ?",
                (site_code, submission_id)
        ) as cursor:
            row = next(cursor, None)
            if not row:
                return None
            return DBCacheEntry(
                site_code,
                submission_id,
                bool(row["is_photo"]),
                row["media_id"],
                row["access_hash"],
                row["file_url"],
                row["caption"],
                dateutil.parser.parse(row["cache_date"]),
                bool(row["full_image"]),
            )

    def save_cache_entry(self, entry: DBCacheEntry) -> None:
        self._just_execute(
            "INSERT INTO cache_entries "
            "(site_code, submission_id, is_photo, media_id, access_hash, file_url, caption, cache_date, full_image) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (site_code, submission_id) "
            "DO UPDATE SET is_photo=excluded.is_photo, media_id=excluded.media_id, access_hash=excluded.access_hash, "
            "file_url=excluded.file_url, caption=excluded.caption, cache_date=excluded.cache_date, "
            "full_image=excluded.full_image",
            (
                entry.site_code, entry.submission_id, entry.is_photo, entry.media_id, entry.access_hash, entry.file_url,
                entry.caption, entry.cache_date.isoformat(), entry.full_image,
            )
        )
