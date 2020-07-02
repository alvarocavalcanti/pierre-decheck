import json
import requests
import os
import logging
import hmac
import hashlib
import urllib.parse
import datetime
from flask_api.status import HTTP_200_OK

STATUS_FAILURE = 'failure'
STATUS_SUCCESS = 'success'
BASE_GITHUB_URL = 'https://api.github.com/'
KEYWORDS_DEPENDS_ON = "depends on"
CONTEXT = "ci/pierre-decheck"
TARGET_URL = "https://{}/details?info={}"
HEADERS = {'Authorization': 'Token {}'.format(os.getenv("GITHUB_TOKEN", ""))}
GITHUB_SECRET = os.getenv("GITHUB_SECRET", "").encode('utf-8')
USE_GITHUB_SECRET = os.getenv("USE_GITHUB_SECRET", False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def check(payload, headers, host):
    verification, reply = verify_source_is_github(payload, headers)
    if not verification:
        return reply

    if not has_pull_request(payload):
        return {"statusCode": 201, "body": "Check has skipped because request body does not contain pull_request."}

    return run_check(payload, host)


def run_check(payload, host):
    owner, repo = get_owner_and_repo(payload)
    bodies = get_all_bodies(payload)
    this_pr_id = get_pull_request_id(payload)
    dependencies = get_dependencies_from_bodies(bodies, this_pr_id)
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
            if state in ["open", "closed_not_released"]:
                are_dependencies_met = False

        logger.info("Updating commit status...")
        update_commit_status(
            owner=owner,
            repo=repo,
            sha=sha,
            dependencies=dependencies_and_states,
            host=host,
            are_dependencies_met=are_dependencies_met
        )

    return {"statusCode": 201, "body": ""}


def _get_digest(secret, data):
    paybytes = urllib.parse.urlencode(data).encode('utf8')
    return hmac.new(
        secret, paybytes,
        hashlib.sha1).hexdigest() if secret else None


def verify_source_is_github(data, headers):
    if USE_GITHUB_SECRET:
        if data is None:
            return False, {"statusCode": 400, "body": "Request body must contain json"}

        digest = _get_digest(GITHUB_SECRET, data)
        if digest is not None:
            header_signature = headers.get("X-Hub-Signature")
            sig_parts = header_signature.split('=', 1)

            if not isinstance(digest, str):
                digest = str(digest)

            if len(sig_parts) < 2 or sig_parts[0] != 'sha1' or not hmac.compare_digest(sig_parts[1], digest):
                return False, {"statusCode": 400, "body": "Invalid Signature"}

    # Implement ping
    event = headers.get('X-GitHub-Event', 'ping')
    if event == 'ping':
        return False, {"statusCode": 200, "body": {'msg': 'pong'}}

    return True, {}


def get_all_bodies(data):
    bodies_from_event = get_bodies(data)
    bodies_from_comments = get_bodies_from_pr_comments(data)
    bodies = []
    bodies.extend(bodies_from_event)
    bodies.extend(bodies_from_comments)
    logger.info(f"Bodies: {bodies}")
    return bodies


def get_sha(data):
    try:
        pr_url = data.get("pull_request").get("url")
    except AttributeError:
        try:
            pr_url = data.get("issue").get("pull_request").get("url")
        except AttributeError:
            pr_url = data.get("issue").get("url")

    commits_url = "{}/commits".format(pr_url)
    response = requests.request('GET', commits_url, headers=HEADERS)

    if response.status_code == HTTP_200_OK:
        logger.info("SHA list: " + response.text)
        commits = json.loads(response.text)
        sorted_commits = sorted(commits, key=lambda x: datetime.datetime.strptime(
            x['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ'), reverse=True)
        return sorted_commits[0].get("sha", None)
    else:
        logger.info("Failed to retrieve SHA information ({}) for {}".format(response.status_code, commits_url))
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
    else:
        logger.info("Failed to retrieve comments information ({}) for {}".format(response.status_code, comments_url))

    return []


def get_bodies(event_object):
    bodies = []
    for key, value in list(event_object.items()):
        if isinstance(value, dict):
            bodies.extend(get_bodies(value))
        elif key == "body":
            bodies.append(value)

    return bodies


def has_pull_request(event):
    if "pull_request" in event:
        return True
    elif "issue" in event:
        return "pull_request" in event.get("issue")
    else:
        return False


def get_pull_request_id(event):
    if "pull_request" in event:
        pr_id = event.get("pull_request").get("number")
    elif "issue" in event:
        pr_id = event.get("issue").get("number")
    else:
        return None

    logger.info(f'Pull Request ID: {pr_id}')
    return pr_id


def get_dependencies_from_bodies(bodies, root_id):
    dependencies = []
    for body in bodies:
        deps = extract_dependency_id(body)
        if deps:
            deps = [dependency_id for dependency_id in deps if dependency_id != root_id]
            dependencies.extend(deps)

    logger.info(f"Dependencies: {list(set(dependencies))}")
    return list(set(dependencies))


def get_owner_and_repo(event):
    repo = event.get("repository", {}).get("name", "")
    owner = event.get("repository", {}).get("owner", {}).get("login", "")
    logger.info(f"Repo: {repo}, Owner: {owner}")

    return owner, repo


def extract_dependency_id(comment_body):
    import re
    comment_body = comment_body.lower()
    regex = (
        r"{}(?:https\:\/\/github\.com\/)?([A-Za-z0-9-_]+\/[A-Za-z0-9-_]+)?(?:\#|\/issues\/|\/pull\/)(\d+)"
        .format("depends on ")
    )
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
    regex = r"([A-Za-z0-9-_]+)\/([A-Za-z0-9-_]+)\#(\d+)"
    match = re.findall(regex, dependency_id)
    if match:
        owner, repo, dependency_id = match[0]
        return owner, repo, dependency_id


def issue_has_release_label(issue, label):
    labels = json.loads(issue).get('labels', [])
    labels_descriptions = [label.get("name", "").lower() for label in labels]
    logging.info(f"Release Label: {label} - PR Labels: {labels}")
    return label in labels_descriptions


def get_dependency_state(dependency_id, owner, repo):
    if is_external_dependency(dependency_id):
        owner, repo, dependency_id = get_external_owner_and_repo(dependency_id)

    url = "{}repos/{}/{}/issues/{}".format(
        BASE_GITHUB_URL,
        owner,
        repo,
        dependency_id
    )
    logger.info(f"URL for Dependency: {url}")
    response = requests.request('GET', url, headers=HEADERS)
    if response.status_code == HTTP_200_OK:
        state = json.loads(response.text).get('state', None)
        if state and state == "closed":
            release_label = os.getenv("RELEASE_LABEL", None)
            if release_label and not issue_has_release_label(issue=response.text, label=release_label.lower()):
                return "closed_not_released"
        return state
    else:
        logger.info("Failed to retrieve dependency information ({}) for {}".format(response.status_code, url))
    return None


def update_commit_status(owner, repo, sha, dependencies, host, are_dependencies_met=False):
    try:
        state = STATUS_SUCCESS if are_dependencies_met else STATUS_FAILURE
        description = "All dependencies are met: {}" if are_dependencies_met else "Not all dependencies are met: {}"
        description = description.format(
            ', '.join('({}: {})'.format(*dep) for dep in dependencies))
        target_url = TARGET_URL.format(host, '-'.join('{}:{}'.format(*dep) for dep in dependencies))

        url = "{}repos/{}/{}/statuses/{}".format(
            BASE_GITHUB_URL,
            owner,
            repo,
            sha
        )

        data = {
            "state": state,
            "target_url": target_url,
            "description": description,
            "context": CONTEXT
        }

        logger.info("Update commit status: URL: {} \n Data: {}".format(url, data))

        response = requests.request('POST', url, headers=HEADERS, data=json.dumps(data))

        logger.info(
            "Update status code: {}, response data: {}".format(response.status_code,
                                                               response.text))
    except Exception:
        logger.error("Problem with updating commit", exc_info=True)


def is_external_dependency(dependency):
    return "#" in dependency


def update_dependants(payload, headers, host):
    merged = headers.get('X-GitHub-Event') == 'pull_request' and payload.get('pull_request').get('merged', False)
    closed_or_reopened = headers.get('X-GitHub-Event') == 'issues' and payload.get('action') in ['closed', 'reopened']
    logger.info("update_dependants: merged: {}, closed: {}".format(merged, closed_or_reopened))
    if not (merged or closed_or_reopened):
        return

    pr_or_issue = 'pull_request' if merged else 'issue'
    timeline_url = "{}repos/{}/issues/{}/timeline?per_page=100".format(
        BASE_GITHUB_URL,
        payload.get('repository').get('full_name'),
        payload.get(pr_or_issue).get('number')
    )

    preview_headers = dict(HEADERS, Accept='application/vnd.github.mockingbird-preview')
    response = requests.request('GET', timeline_url, headers=preview_headers)
    if response.status_code != HTTP_200_OK:
        logger.info("Failed to retrieve PR timeline for {} : {}".format(timeline_url, response.text))
        return

    logger.info("Timeline response: {}".format(response.text))
    timeline = json.loads(response.text)
    x_ref_events = list(filter(lambda x: x['event'] == 'cross-referenced', timeline))
    pr_events = list(filter(lambda x: 'pull_request' in x['source']['issue'], x_ref_events))
    open_pr_events = list(filter(lambda x: x['source']['issue']['state'] != 'closed', pr_events))
    logger.info("{} cross-referenced PR found.".format(len(open_pr_events)))

    for pr in open_pr_events:
        run_check(pr.get('source').get('issue'), host)
