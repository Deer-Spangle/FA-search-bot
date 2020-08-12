import logging
import sys
from datetime import datetime
from typing import Optional

import requests

api_url = "https://faexport.spangle.org.uk"

last_known_good_id = 9_582_614
max_jump = 10
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("{asctime}:{levelname}:{name}:{message}", style="{")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_journal_title(journal_id: int) -> Optional[str]:
    url = f"{api_url}/journal/{journal_id}.json"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()["title"]
    return None


start_time = datetime.now()
while True:
    try_id = last_known_good_id + 1
    missing_journals = []
    logger.debug("FROM THE START")
    while try_id < last_known_good_id + max_jump:
        title = get_journal_title(try_id)
        if title is None:
            missing_journals.append(try_id)
        else:
            last_known_good_id = try_id
            for missing_id in missing_journals:
                logger.info(f"{missing_id}:---")
            logger.info(f"{try_id}: {title}   - ({(datetime.now()-start_time).total_seconds()})")
            start_time = datetime.now()
            missing_journals = []
        try_id += 1
