import json
import os


from lib.pierre import check

GITHUB_SECRET = os.getenv("GITHUB_SECRET", "").encode('utf-8')


def pierre_decheck(event, context):
    event_data = json.loads(event.get("body"))
    return check(event_data)


