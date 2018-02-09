import json

import requests
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


@app.route("/prcomment", methods=['POST'])
def pull_request_comment():
    print("Received request with headers \n{} \n and data: \n{}".format(request.headers, request.data))
    if _does_not_have_github_headers():
        print("Could not find GitHub headers")
        return {"message": "Could not find GitHub headers"}, status.HTTP_400_BAD_REQUEST

    dependency_id = _get_dependency_id_if_comment_has_keywords(KEYWORDS_DEPENDS_ON)
    print("Comment has keywords? {}".format(dependency_id))
    if dependency_id:
        owner, repo, sha = _extract_comment_info()
        print("Comment Info: owner {}, repo {}, sha {}".format(owner, repo, sha))
        set_status(owner, repo, sha, STATUS_PENDING, DESCRIPTION_PENDING)
        dependency_state = check_dependency(dependency_id, owner, repo)
        print("Dependency State: {}".format(dependency_state))
        if dependency_state:
            update_commit_status(owner, repo, sha, dependency_state)

    return {}, status.HTTP_201_CREATED


def _get_dependency_id_if_comment_has_keywords(keywords):
    import re
    comment_body = request.data.get('comment', {}).get("body", "").lower()
    regex = r"(?:{}).(?:\#)(\d*)".format(keywords)
    match = re.search(regex, comment_body)
    if match:
        return match.group(1)
    return False


def _extract_comment_info():
    owner = request.data.get('repository', {}).get('owner', {}).get('login', '')
    repo = request.data.get('repository', {}).get('name', '')
    sha = request.data.get('comment', {}).get('commit_id', '')
    return owner, repo, sha


def _does_not_have_github_headers():
    has_github_delivery, has_github_event, has_github_user_agent = _extract_github_headers()
    return not (has_github_delivery and has_github_event and has_github_user_agent)


def _extract_github_headers():
    has_github_event = request.headers.get('X-GitHub-Event', '') == 'issue_comment'
    has_github_delivery = True if request.headers.get('X-GitHub-Delivery', '') else False
    has_github_user_agent = request.headers.get('User-Agent', '').startswith('GitHub-')
    return has_github_delivery, has_github_event, has_github_user_agent


def set_status(owner, repo, sha, commit_status, description=None):
    url = '{}repos/{}/{}/statuses/{}'.format(
        BASE_GITHUB_URL,
        owner,
        repo,
        sha
    )

    payload = {
        "state": commit_status,
        "target_url": "foo",
        "description": description,
        "context": "continuous-integration/merge-watcher"
    }

    requests.request('POST', url, data=json.dumps(payload))


def check_dependency(dependency_id, owner, repo):
    url = "{}repos/{}/{}/issues/{}".format(
        BASE_GITHUB_URL,
        owner,
        repo,
        dependency_id
    )

    response = requests.request('GET', url)

    if response.status_code == status.HTTP_200_OK:
        return json.loads(response.text).get('state', None)

    return None


def update_commit_status(owner, repo, sha, dependency_state):
    if dependency_state == "open":
        state = "failure"
        description = DESCRIPTION_OPEN
    elif dependency_state == "closed":
        state = "success"
        description = DESCRIPTION_CLOSED
    else:
        state = "pending"
        description = DESCRIPTION_PENDING

    url = "{}repos/{}/{}/statuses/{}".format(
        BASE_GITHUB_URL,
        owner,
        repo,
        sha
    )

    data = {
        "state": state,
        "target_url": "foo",
        "description": description,
        "context": CONTEXT
    }

    requests.request('POST', url, data=json.dumps(data))


if __name__ == "__main__":
    app.run(debug=True)
