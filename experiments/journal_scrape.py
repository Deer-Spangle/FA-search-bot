import logging
import sys
from datetime import datetime
from typing import Optional

import requests

api_url = "https://faexport.spangle.org.uk"

last_known_good_id = 9_750_190
max_jump = 10
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("{asctime}:{levelname}:{name}:{message}", style="{")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

####
# This experiment is to test out a method of scraping new journals.
# It has a downside that it may lock up if a certain number of journals are created and deleted in a row before being
# scraped. Therefore an alert needs setting up, using the standard heartbeat server. This script is therefore noting
# the number of seconds between new journal posts, in order to set an alert timeout large enough to avoid false
# positives, while being small enough to be alert before reasonable downtime.
# Heartbeat server would need to be pinged each time a new journal was found, not every time the loop is ran.
####
# Results
# - I recorded new journal posts for 1.4 days, across a Thursday evening and Friday
# - Over that time there were 1314 journal posts, and the maximum time between journal posts was 1102.02 seconds.
# - If the timeout was set to 5 minutes, the default for heartbeat server, there would have been 61 false alarms
# during the testing period.
# - - If the timeout was set to 10 minutes, there would have been 10 false alarms.
# - - If the timeout was set to 15 minutes, there would have been 2 false alarms.
# - - If the timeout was set to 30 minutes, there would have been zero false alarms.
# - I recommend the heartbeat timeout is set to 30 or 60 minutes.
# - It is possible one could automate posting a new journal after that long, in order to the latest journal ID, but
# this is additional complexity that may not be warranted.
# - The spreadsheet of results is available here:
# https://docs.google.com/spreadsheets/d/1o2U4g_OB2ZqZTRLoMg3-HZmPsT763fylWoCW59zeBbE/edit#gid=0
####


def get_journal_title(journal_id: int) -> Optional[str]:
    url = f"{api_url}/journal/{journal_id}.json"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()["title"]
    return None


start_time = datetime.now()
caught_up = False
timings_between_new_journals = None
while True:
    if caught_up and timings_between_new_journals is None:
        timings_between_new_journals = []
    try_id = last_known_good_id + 1
    missing_journals = []
    logger.debug("FROM THE START")
    caught_up = True
    while try_id < last_known_good_id + max_jump:
        title = get_journal_title(try_id)
        if title is None:
            missing_journals.append(try_id)
        else:
            last_known_good_id = try_id
            for missing_id in missing_journals:
                logger.info(f"{missing_id}:---")
            time_between = (datetime.now()-start_time).total_seconds()
            logger.info(f"{try_id}: {title}   - ({time_between})")
            if timings_between_new_journals is not None:
                timings_between_new_journals.append(time_between)
                logger.info(f"All timings: {timings_between_new_journals}")
            start_time = datetime.now()
            missing_journals = []
        try_id += 1
