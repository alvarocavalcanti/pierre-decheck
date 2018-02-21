import json

from flask import request

from flask_api import FlaskAPI, status

app = FlaskAPI(__name__)

STATUS_ERROR = 'error'
STATUS_FAILURE = 'failure'
STATUS_PENDING = 'pending'
STATUS_SUCCESS = 'success'
BASE_GITHUB_URL = 'https://api.github.com/'
KEYWORDS_DEPENDS_ON = "depends on"
CONTEXT = "continuous-integration/merge-watcher"
DESCRIPTION_PENDING = "Checking dependencies..."
DESCRIPTION_OPEN = "Dependencies are still open."
DESCRIPTION_CLOSED = "Dependencies are satisfied."


@app.route("/", methods=['GET', 'POST'])
def root_list():
    return "Pierre DeCheck: nothing to see here.", status.HTTP_200_OK


@app.route("/webhook", methods=['POST'])
def webhook_event():
    print("Received request with headers \n{} \n and data: \n{}".format(request.headers, request.data))

    return {}, status.HTTP_201_CREATED


def get_bodies(event_object):
    bodies = []
    for key, value in event_object.items():
        if isinstance(value, dict):
            bodies.extend(get_bodies(value))
        elif key == "body":
            bodies.append(value)

    return bodies


def get_dependencies_from_bodies(bodies):
    dependencies = [_get_dependency_ids(body) for body in bodies]
    return [dep for dep in dependencies if dep]


def _get_dependency_ids(comment_body):
    import re
    comment_body = comment_body.lower()
    regex = r"(?:{}).(?:\#)(\d*)".format("depends on")
    match = re.search(regex, comment_body)
    if match:
        return match.group(1)


if __name__ == "__main__":
    app.run(debug=True)
