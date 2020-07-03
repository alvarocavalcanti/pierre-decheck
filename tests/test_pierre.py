import json
import os
from unittest.mock import patch, Mock

from flask_api.status import HTTP_200_OK

from lib.payloads import PR_COMMENT_EVENT, PR_CREATED, ISSUE_DETAIL
from lib.pierre import (
    get_bodies,
    get_dependencies_from_bodies,
    is_external_dependency,
    get_external_owner_and_repo,
    get_owner_and_repo,
    BASE_GITHUB_URL,
    check,
    HEADERS,
    get_dependency_state,
    update_dependants,
    get_sha,
)
from tests.pierre import PierreTestCase

GITHUB_HEADERS = {
    "X-GitHub-Event": "issue_comment",
    "X-GitHub-Delivery": "foo",
    "User-Agent": "GitHub-Foo"
}

HOST = "infinite-harbor-38537.herokuapp.com"


class TestPierre(PierreTestCase):

    def test_get_bodies_from_pr_comment_event(self):
        bodies = get_bodies(json.loads(PR_COMMENT_EVENT))

        self.assertEqual(2, len(bodies))
        self.assertEqual("This is the PR body", bodies[0])
        self.assertEqual("this is a comment", bodies[1])

    def test_get_bodies_from_pr_created_event(self):
        bodies = get_bodies(json.loads(PR_CREATED))

        self.assertEqual(1, len(bodies))
        self.assertEqual("This is the PR body", bodies[0])

    def test_get_dependencies_identifiers_from_list(self):
        bodies = ["Depends on #2", "", "depends on #3", "No dependencies here", "depends on #4"]

        root_id = '4'
        dependencies = get_dependencies_from_bodies(bodies, root_id)

        self.assertEqual(2, len(dependencies))
        self.assertIn("2", dependencies)
        self.assertIn("3", dependencies)

    def test_get_dependencies_identifiers_from_single_body(self):
        bodies = ["Depends on #2. Depends on #3"]

        root_id = '4'
        dependencies = get_dependencies_from_bodies(bodies, root_id)

        self.assertEqual(2, len(dependencies))
        self.assertIn("2", dependencies)
        self.assertIn("3", dependencies)

    def test_get_dependencies_removes_duplicates(self):
        bodies = ["Depends on #2", "", "depends on #3", "depends on #3"]

        root_id = '4'
        dependencies = get_dependencies_from_bodies(bodies, root_id)

        self.assertEqual(2, len(dependencies))

    def test_get_dependencies_accepts_external_dependencies(self):
        bodies = ["Depends on #2", "", "depends on alvarocavalcanti/my-dev-templates#1"]

        root_id = '4'
        dependencies = get_dependencies_from_bodies(bodies, root_id)

        self.assertEqual(2, len(dependencies))
        self.assertIn("2", dependencies)
        self.assertIn("alvarocavalcanti/my-dev-templates#1", dependencies)

    def test_is_external_dependency(self):
        self.assertTrue(is_external_dependency("alvarocavalcanti/my-dev-templates#1"))
        self.assertFalse(is_external_dependency("1"))

    def test_get_external_owner_and_repo(self):
        owner, repo, dependency_id = get_external_owner_and_repo("alvarocavalcanti/my-dev-templates#1")

        self.assertEqual("alvarocavalcanti", owner)
        self.assertEqual("my-dev-templates", repo)
        self.assertEqual("1", dependency_id)

    def test_get_owner_and_repo_from_pr_comment_event(self):
        owner, repo = get_owner_and_repo(json.loads(PR_COMMENT_EVENT))

        self.assertEqual("alvarocavalcanti", owner)
        self.assertEqual("pierre-decheck", repo)

    def test_get_owner_and_repo_from_pr_created_event(self):
        owner, repo = get_owner_and_repo(json.loads(PR_CREATED))

        self.assertEqual("alvarocavalcanti", owner)
        self.assertEqual("pierre-decheck", repo)

    @patch('lib.pierre.requests.request')
    def test_checks_dependencies_upon_receiving_pr_created_event(self, requests_mock):
        payload = json.loads(PR_CREATED.replace("This is the PR body", "This is the PR body. Depends on #2."))

        response = check(payload, headers=GITHUB_HEADERS, host=HOST)

        self.assertEqual(201, response.get("statusCode"))

        expected_url = "{}repos/{}/{}/issues/{}".format(
            BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "2"
        )

        requests_mock.assert_any_call('GET', expected_url, headers=HEADERS)

    @patch('lib.pierre.requests.request')
    def test_checks_dependencies_upon_receiving_pr_comment_event_for_more_than_one_dependency(
            self, requests_mock
    ):
        payload = PR_COMMENT_EVENT.replace("This is the PR body", "Depends on #2.")
        payload = json.loads(payload.replace("this is a comment", "Depends on #3."))

        response = check(payload, headers=GITHUB_HEADERS, host=HOST)

        self.assertEqual(201, response.get("statusCode"))

        expected_url_dep_2 = "{}repos/{}/{}/issues/{}".format(
            BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "2"
        )

        expected_url_dep_3 = "{}repos/{}/{}/issues/{}".format(
            BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "3"
        )

        requests_mock.assert_any_call('GET', expected_url_dep_2, headers=HEADERS)
        requests_mock.assert_any_call('GET', expected_url_dep_3, headers=HEADERS)

    @patch('lib.pierre.requests.request')
    def test_checks_dependencies_upon_receiving_pr_comment_event_for_more_than_one_dependency_on_external_repo(
            self, requests_mock
    ):
        payload = PR_COMMENT_EVENT.replace("This is the PR body", "Depends on owner/repo#2.")
        payload = json.loads(payload.replace("this is a comment", (
            "Depends on https://github.com/owner/repo/pull/3."
            "Depends on https://github.com/owner/repo/issues/4."
        )))

        response = check(payload, headers=GITHUB_HEADERS, host=HOST)

        self.assertEqual(201, response.get("statusCode"))

        expected_url_dep_2 = "{}repos/{}/{}/issues/{}".format(
            BASE_GITHUB_URL,
            "owner",
            "repo",
            "2"
        )

        expected_url_dep_3 = "{}repos/{}/{}/issues/{}".format(
            BASE_GITHUB_URL,
            "owner",
            "repo",
            "3"
        )

        expected_url_dep_4 = "{}repos/{}/{}/issues/{}".format(
            BASE_GITHUB_URL,
            "owner",
            "repo",
            "4"
        )

        requests_mock.assert_any_call('GET', expected_url_dep_2, headers=HEADERS)
        requests_mock.assert_any_call('GET', expected_url_dep_3, headers=HEADERS)
        requests_mock.assert_any_call('GET', expected_url_dep_4, headers=HEADERS)

    @patch("requests.request")
    @patch.dict(os.environ, {'RELEASE_LABEL': 'RELEASED'})
    def test_gets_dependency_state_as_open_when_issue_is_closed_but_has_not_been_released(self, mock_request):
        request_response = Mock()
        request_response.status_code = HTTP_200_OK
        issue_detail = ISSUE_DETAIL.replace("ISSUE_STATUS", "closed")
        request_response.text = issue_detail

        mock_request.return_value = request_response

        issue_state = get_dependency_state("1", "foo", "bar")

        self.assertEqual("closed_not_released", issue_state)

    @patch("requests.request")
    @patch.dict(os.environ, {'RELEASE_LABEL': 'RELEASED'})
    def test_gets_dependency_state_as_closed_when_issue_is_closed_and_has_been_released(self, mock_request):
        request_response = Mock()
        request_response.status_code = HTTP_200_OK
        issue_detail = ISSUE_DETAIL.replace("ISSUE_STATUS", "closed")
        issue_detail = issue_detail.replace("LABEL_NAME", "RELEASED")
        request_response.text = issue_detail

        mock_request.return_value = request_response

        issue_state = get_dependency_state("1", "foo", "bar")

        self.assertEqual("closed", issue_state)

    @patch('lib.pierre.run_check')
    @patch('lib.pierre.requests.request')
    def test_update_dependants_upon_receiving_pr_merged_event(self, requests_mock, run_check_mock):
        request_response = Mock()
        request_response.status_code = HTTP_200_OK
        request_response.text = open('tests/payloads/response/issues/timeline.json').read()
        requests_mock.return_value = request_response

        headers = dict(GITHUB_HEADERS, **{"X-GitHub-Event": "pull_request"})
        payload = json.loads(open('tests/payloads/webhook/pull_request/closed.json').read())

        update_dependants(payload, headers=headers, host=HOST)

        expected_url = "{}repos/{}/{}/issues/{}/timeline?per_page=100".format(
            BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "16"
        )

        headers = dict(HEADERS, Accept='application/vnd.github.mockingbird-preview')
        requests_mock.assert_any_call('GET', expected_url, headers=headers)

        timeline = json.loads(open('tests/payloads/response/issues/timeline.json').read())
        pr = timeline[-1].get('source').get('issue')
        run_check_mock.assert_called_once_with(pr, HOST)

    @patch('lib.pierre.run_check')
    @patch('lib.pierre.requests.request')
    def test_update_dependants_upon_receiving_issue_reopened_event(self, requests_mock, run_check_mock):
        request_response = Mock()
        request_response.status_code = HTTP_200_OK
        request_response.text = open('tests/payloads/response/issues/timeline.json').read()
        requests_mock.return_value = request_response

        headers = dict(GITHUB_HEADERS, **{"X-GitHub-Event": "issues"})
        payload = json.loads(open('tests/payloads/webhook/issues/reopened.json').read())

        update_dependants(payload, headers=headers, host=HOST)

        expected_url = "{}repos/{}/{}/issues/{}/timeline?per_page=100".format(
            BASE_GITHUB_URL,
            "Codertocat",
            "Hello-World",
            "1"
        )

        headers = dict(HEADERS, Accept='application/vnd.github.mockingbird-preview')
        requests_mock.assert_any_call('GET', expected_url, headers=headers)

        timeline = json.loads(open('tests/payloads/response/issues/timeline.json').read())
        pr = timeline[-1].get('source').get('issue')
        run_check_mock.assert_called_once_with(pr, HOST)

    @patch('lib.pierre.run_check')
    @patch('lib.pierre.requests.request')
    def test_not_update_dependants_upon_receiving_pr_closed_event(self, requests_mock, run_check_mock):
        headers = dict(GITHUB_HEADERS, **{"X-GitHub-Event": "pull_request"})
        payload = json.loads(open('tests/payloads/webhook/pull_request/closed.json').read())
        payload['pull_request']['merged'] = False

        update_dependants(payload, headers=headers, host=HOST)

        requests_mock.assert_not_called()
        run_check_mock.assert_not_called()

    @patch('lib.pierre.run_check')
    @patch('lib.pierre.requests.request')
    def test_not_update_dependants_for_closed_pr(self, requests_mock, run_check_mock):
        request_response = Mock()
        request_response.status_code = HTTP_200_OK
        timeline = json.loads(open('tests/payloads/response/issues/timeline.json').read())
        timeline[-1]['source']['issue']['state'] = 'closed'
        request_response.text = json.dumps(timeline)
        requests_mock.return_value = request_response

        headers = dict(GITHUB_HEADERS, **{"X-GitHub-Event": "pull_request"})
        payload = json.loads(open('tests/payloads/webhook/pull_request/closed.json').read())

        update_dependants(payload, headers=headers, host=HOST)

        expected_url = "{}repos/{}/{}/issues/{}/timeline?per_page=100".format(
            BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "16"
        )

        headers = dict(HEADERS, Accept='application/vnd.github.mockingbird-preview')
        requests_mock.assert_any_call('GET', expected_url, headers=headers)

        run_check_mock.assert_not_called()

    @patch('lib.pierre.run_check')
    @patch('lib.pierre.requests.request')
    def test_not_update_dependants_for_issue(self, requests_mock, run_check_mock):
        request_response = Mock()
        request_response.status_code = HTTP_200_OK
        timeline = json.loads(open('tests/payloads/response/issues/timeline.json').read())
        del timeline[-1]['source']['issue']['pull_request']
        request_response.text = json.dumps(timeline)
        requests_mock.return_value = request_response

        headers = dict(GITHUB_HEADERS, **{"X-GitHub-Event": "pull_request"})
        payload = json.loads(open('tests/payloads/webhook/pull_request/closed.json').read())

        update_dependants(payload, headers=headers, host=HOST)

        expected_url = "{}repos/{}/{}/issues/{}/timeline?per_page=100".format(
            BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "16"
        )

        headers = dict(HEADERS, Accept='application/vnd.github.mockingbird-preview')
        requests_mock.assert_any_call('GET', expected_url, headers=headers)

        run_check_mock.assert_not_called()

    @patch("requests.request")
    def test_get_sha_from_pr_created_event(self, mock_request):
        payload = json.loads(PR_CREATED)

        sha = get_sha(payload)

        self.assertEqual(payload.get("pull_request").get("head").get("sha"), sha)

        mock_request.assert_not_called()

    @patch("requests.request")
    def test_get_sha_from_pr_comment_event(self, mock_request):
        request_response = Mock()
        request_response.status_code = HTTP_200_OK
        request_response.text = '{"head":{"sha":"expected-sha"}}'

        mock_request.return_value = request_response

        expected_url = "{}repos/{}/{}/pulls/{}".format(
            BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "28"
        )

        sha = get_sha(json.loads(PR_COMMENT_EVENT))

        self.assertEqual("expected-sha", sha)

        mock_request.assert_called_once_with('GET', expected_url, headers=HEADERS)
