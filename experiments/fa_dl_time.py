import requests
import timeit
from fa_search_bot.sites.sendable import _downloaded_file
import random

####
# This experiment dates to 2023-05-17, and I do not have the results from then, but it's a test to see how fast it is to
# download a batch of random submissions from FA.
####

thumb_links = []
full_dl_links = []

home_resp = requests.get("https://faexport.spangle.org.uk/browse.json")
home_json = home_resp.json()
for home_item in home_json:
    thumb_links.append(home_item["thumbnail"])
    print(".", end="", flush=True)
    sub_json = requests.get(f"https://faexport.spangle.org.uk/submission/{home_item['id']}.json").json()
    full_dl_links.append(sub_json["download"])

print("")

print(f"Got {len(thumb_links)} links to test")

def dl_test(url: str):
    with _downloaded_file(url) as dl_file:
        pass

random.shuffle(full_dl_links)

results = []

for link in full_dl_links:
    t = timeit.Timer(
        f"dl_test(\"{link}\")",
        setup="from __main__ import dl_test",
    )
    print(t.timeit(5))
