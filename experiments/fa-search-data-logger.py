import time

import requests
import datetime

API_URL = "http://localhost:9292/"
SEARCH_TERM = "ych"

####
# This is an experiment to observe FA search. This script checks the FA search for SEARCH_TERM once every minute, and
# records which submissions are added, and deleted, each minute. It logs this information to a file, along with whether
# the length of the results list changes.
###
# Results
# So, using this script, I have found that:
# - FA search updates its index and adds new results every 5 minutes.
# - The length of the returned list can drop between these re-indexes, if submissions are removed.
# - - List will return to 72 elements at the next re-index
# - Between ~08:15 and 08:45 (BST), the search results become erratic.
# - - The number of results on a page drops dramatically at about 08:15, from specified 72 to about 20-30
# - - During this time, the results are all from 24 hours ago
# - - During this time, the number of results steadily increases, reaching maybe 30-40 before springing back to 72
###


def log(line):
    line = f"{datetime.datetime.now().isoformat()}: {line}"
    with open("log.txt", "a+") as f:
        f.write(line+"\n")
    print(line)


last_set = None
while True:
    time.sleep(60)
    resp = requests.get(f"{API_URL}/search.json?q={SEARCH_TERM}&perpage=72")
    set_ids = set(resp.json())
    if last_set is None:
        log(f"Starting watcher, first list: {set_ids}")
        last_set = set_ids
        continue
    new = set_ids - last_set
    lost = last_set - set_ids
    if len(set_ids) != len(last_set):
        log(f"Results length changed. Was {len(last_set)}, now {len(set_ids)}")
    if len(new) != 0:
        log(f"New results: {new}")
    if len(lost) != 0:
        log(f"Lost results: {lost}")
    log("---")
    last_set = set_ids
