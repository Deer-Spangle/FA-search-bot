import requests

####
# This is an experiment to determine which thumbnail sizes are valid on FA, and which will redirect to a different size.
# This seemed necessary as the bot currently (of writing) assumes FA will serve up a 1600px thumbnail, but tht seems
# to redirect to 600px thumbnails now.
###
# Results (2022-11-28)
# So, using this script, I have found that valid thumbnail sizes, in pixels are:
# 50, 75, 100, 120, 150, 200, 250, 300, 320, 400, 600
# There are no other valid thumbnail sizes under 2000 pixels
###
# Results (2023-09-03)
# Re-running this script now, the set of thumbnail sizes has been reduced once again.
# Now the only valid sizes are:
# 200, 300, 400, 600
###

for size in range(5, 2000, 5):
    thumb_url = f"https://t.furaffinity.net/19925704@{size}-1462827244.jpg"
    resp = requests.head(thumb_url)
    if resp.status_code == 200:
        print(f"Valid thumbnail size: {size}")
    else:
        print(".", end="")
