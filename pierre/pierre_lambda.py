import json
from lib.pierre import check


def pierre_decheck(event, context):
    event_data = json.loads(event.get("body"))
    headers = json.loads(event.get("headers"))
    host = json.loads(event.get("environ").get("HTTP_HOST"))
    return check(event_data, headers, host)


