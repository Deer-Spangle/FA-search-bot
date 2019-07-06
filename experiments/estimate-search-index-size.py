import json
import random

import requests

API_URL = "http://localhost:9292/"
RANDOM_SAMPLE_SIZE = 1000

####
# This experiment is to try and estimate the size of a theoretical search index for FA, including keywords, title, and
# description for all submissions on the site.
# This would be handy, to skip FA's flaky search system
####
# Results
# - Looks like that data would be about 11GB (as of 2019-06-28)
# - At a guess, I would say it would take a few hundred days to harvest though.
# - Probably best to use FA's search and skip the silly hours.
####

home_page = requests.get(f"{API_URL}/home.json").json()
highest_id = int(home_page['artwork'][0]['id'])
submission_ids = range(highest_id)
sample = random.sample(submission_ids, RANDOM_SAMPLE_SIZE)
print(f"Chosen sample: ")

submission_data = {}
for submission_id in sample:
    print(f"Getting: {submission_id}")
    submission_resp = requests.get(f"{API_URL}/submission/{submission_id}.json")
    if submission_resp.status_code != 200:
        short_submission = None
    else:
        submission = submission_resp.json()
        short_submission = {
            'id': submission_id,
            'title': submission['title'],
            'description': submission['description'],
            'keywords': submission['keywords']
        }
    submission_data[submission_id] = short_submission

submission_json = json.dumps(submission_data)
sample_data_size = len(submission_json)
print(f"Sample data ended up being: "
      f"{sample_data_size} bytes. {sample_data_size/1024}KB. {sample_data_size/(1024**2)}MB")

estimated_data_size = sample_data_size * highest_id / RANDOM_SAMPLE_SIZE
print(f"Estimating that total data would be: "
      f"{estimated_data_size} bytes. {estimated_data_size/1024}KB. {estimated_data_size/(1024**2)}MB")

print("Finished")
