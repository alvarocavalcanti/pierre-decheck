import json

import requests
from flask import request

from flask_api import FlaskAPI, status

app = FlaskAPI(__name__)

STATUS_FAILURE = 'failure'
STATUS_SUCCESS = 'success'
BASE_GITHUB_URL = 'https://api.github.com/'
KEYWORDS_DEPENDS_ON = "depends on"
CONTEXT = "continuous-integration/pierre-decheck"


@app.route("/", methods=['GET', 'POST'])
def root_list():
    return "Pierre DeCheck: nothing to see here.", status.HTTP_200_OK


@app.route("/webhook", methods=['POST'])
def webhook_event():
    # print("Received request with headers \n{}and data: \n{}".format(request.headers, request.data))
    owner, repo = get_owner_and_repo(request.data)
    bodies = get_bodies(request.data)
    dependencies = get_dependencies_from_bodies(bodies)
    dependencies_and_states = []
    for dep in dependencies:
        state = get_dependency_state(dependency_id=dep, owner=owner, repo=repo)
        dependencies_and_states.append((dep, state))

    print("Owner: {}, Repo: {}. Dependencies: {}".format(
        owner,
        repo,
        dependencies_and_states
    ))

    if dependencies_and_states and len(dependencies_and_states) > 0:
        sha = get_sha(request.data)
        are_dependencies_met = True
        for dep, state in dependencies_and_states:
            if state == "open":
                are_dependencies_met = False

        update_commit_status(
            owner=owner, repo=repo, sha=sha, dependencies=dependencies, are_dependencies_met=are_dependencies_met
        )

    return {}, status.HTTP_201_CREATED


def get_sha(data):
    try:
        pr_url = data.get("pull_request").get("url")
    except AttributeError:
        pr_url = data.get("issue").get("pull_request").get("url")
    commits_url = "{}/commits".format(pr_url)
    response = requests.request('GET', commits_url)
    if response.status_code == status.HTTP_200_OK:
        commits = json.loads(response.text)
        return commits[-1].get("sha", None)
    return None


def get_bodies(event_object):
    bodies = []
    for key, value in event_object.items():
        if isinstance(value, dict):
            bodies.extend(get_bodies(value))
        elif key == "body":
            bodies.append(value)

    return bodies


def get_dependencies_from_bodies(bodies):
    dependencies = []
    for body in bodies:
        deps = extract_dependency_id(body)
        if deps:
            dependencies.extend(deps)

    return [dep for dep in dependencies if dep]


def get_owner_and_repo(event):
    repo = event.get("repository", {}).get("name", "")
    owner = event.get("repository", {}).get("owner", {}).get("login", "")

    return owner, repo


def extract_dependency_id(comment_body):
    import re
    comment_body = comment_body.lower()
    regex = r"(?:{}).(?:\#)(\d*)".format("depends on")
    match = re.findall(regex, comment_body)
    if match:
        return match


def get_dependency_state(dependency_id, owner, repo):
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


def update_commit_status(owner, repo, sha, dependencies, are_dependencies_met=False):
    state = STATUS_SUCCESS if are_dependencies_met else STATUS_FAILURE
    description = "Dependencies #: {}".format(', '.join(dependencies))

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

    print("Update commit status: {}".format(data))

    requests.request('POST', url, data=json.dumps(data))


if __name__ == "__main__":
    app.run(debug=True)
