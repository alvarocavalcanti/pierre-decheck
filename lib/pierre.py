import json
import requests
import os
import logging
import datetime

STATUS_FAILURE = 'failure'
STATUS_SUCCESS = 'success'
BASE_GITHUB_URL = 'https://api.github.com/'
KEYWORDS_DEPENDS_ON = "depends on"
CONTEXT = "ci/pierre-decheck"
TARGET_URL = "https://infinite-harbor-38537.herokuapp.com/details?info={}"
HTTP_200_OK = 200
HEADERS = {'Authorization': 'Token {}'.format(os.getenv("GITHUB_TOKEN", ""))}

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check(payload):
    owner, repo = get_owner_and_repo(payload)
    bodies = get_all_bodies(payload)
    dependencies = get_dependencies_from_bodies(bodies)
    dependencies_and_states = []
    for dep in dependencies:
        state = get_dependency_state(dependency_id=dep, owner=owner, repo=repo)
        dependencies_and_states.append((dep, state))

        logger.info("Owner: {}, Repo: {}. Dependencies: {}".format(
            owner,
            repo,
            dependencies_and_states
        ))

    if len(dependencies) == 0 or (
                dependencies_and_states and len(dependencies_and_states) > 0):
        sha = get_sha(payload)
        are_dependencies_met = True
        for dep, state in dependencies_and_states:
            if state == "open":
                are_dependencies_met = False

        update_commit_status(
            owner=owner,
            repo=repo,
            sha=sha,
            dependencies=dependencies_and_states,
            are_dependencies_met=are_dependencies_met
        )

    return {"statusCode": 201, "body": ""}


def get_all_bodies(data):
    bodies_from_event = get_bodies(data)
    bodies_from_comments = get_bodies_from_pr_comments(data)
    bodies = []
    bodies.extend(bodies_from_event)
    bodies.extend(bodies_from_comments)
    return bodies


def get_sha(data):
    try:
        pr_url = data.get("pull_request").get("url")
    except AttributeError:
        pr_url = data.get("issue").get("pull_request").get("url")

    commits_url = "{}/commits".format(pr_url)
    response = requests.request('GET', commits_url, headers=HEADERS)

    if response.status_code == HTTP_200_OK:
        logger.info("SHA list: " + response.text)
        commits = json.loads(response.text)
        sorted_commits = sorted(commits, key=lambda x: datetime.datetime.strptime(
            x['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ'), reverse=True)
        return sorted_commits[0].get("sha", None)
    return None


def get_bodies_from_pr_comments(event_data):
    try:
        pr_url = event_data.get("pull_request").get("url")
    except AttributeError:
        pr_url = event_data.get("issue").get("url")

    comments_url = "{}/comments".format(pr_url)
    comments_url = comments_url.replace("pulls/", "issues/")

    response = requests.request('GET', comments_url, headers=HEADERS)
    if response.status_code == HTTP_200_OK:
        comments = json.loads(response.text)
        return [comment.get("body") for comment in comments]

    return []


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

    return list(set(dependencies))


def get_owner_and_repo(event):
    repo = event.get("repository", {}).get("name", "")
    owner = event.get("repository", {}).get("owner", {}).get("login", "")

    return owner, repo


def extract_dependency_id(comment_body):
    import re
    comment_body = comment_body.lower()
    regex = r"(?:{})([A-Za-z0-9-_]+\/[A-Za-z0-9-_]+)*(?:\#)(\d*)".format("depends on ")
    match = re.findall(regex, comment_body)
    if match:
        items = []
        for match1, match2 in match:
            if match1:
                item = "{}#{}".format(match1, match2)
            else:
                item = match2
            items.append(item)

        return items


def get_external_owner_and_repo(dependency_id):
    import re
    regex = r"([A-Za-z0-9-_]+)(?:\/)([A-Za-z0-9-_]+)*(?:\#)(\d*)"
    match = re.findall(regex, dependency_id)
    if match:
        owner, repo, dependency_id = match[0]
        return owner, repo, dependency_id


def get_dependency_state(dependency_id, owner, repo):
    if is_external_dependency(dependency_id):
        owner, repo, dependency_id = get_external_owner_and_repo(dependency_id)

    url = "{}repos/{}/{}/issues/{}".format(
        BASE_GITHUB_URL,
        owner,
        repo,
        dependency_id
    )
    response = requests.request('GET', url, headers=HEADERS)
    if response.status_code == HTTP_200_OK:
        return json.loads(response.text).get('state', None)
    return None


def update_commit_status(owner, repo, sha, dependencies, are_dependencies_met=False):
    try:
        state = STATUS_SUCCESS if are_dependencies_met else STATUS_FAILURE
        description = "All dependencies are met: {}" if are_dependencies_met else "Not all dependencies are met: {}"
        description = description.format(
            ', '.join('({}: {})'.format(*dep) for dep in dependencies))

        url = "{}repos/{}/{}/statuses/{}".format(
            BASE_GITHUB_URL,
            owner,
            repo,
            sha
        )

        data = {
            "state": state,
            "target_url": None,
            "description": description,
            "context": CONTEXT
        }

        logger.info("Update commit status: URL: {} \n Data: {}".format(url, data))

        response = requests.request('POST', url, headers=HEADERS, data=json.dumps(data))

        logger.info(
            "Update status code: {}, response data: {}".format(response.status_code,
                                                               response.text))
    except:
        logger.error("Problem with updating commit", exc_info=True)


def is_external_dependency(dependency):
    return "#" in dependency

