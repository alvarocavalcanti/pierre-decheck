import json
import unittest
from unittest.mock import patch

from flask_api import status
from flask_testing import TestCase


import server
from lib.payloads import PR_COMMENT_EVENT, PR_CREATED
from lib import pierre
from lib.pierre import HEADERS as request_headers


class ServerTest(TestCase):
    render_templates = False

    GITHUB_HEADERS = {
        "X-GitHub-Event": "issue_comment",
        "X-GitHub-Delivery": "foo",
        "User-Agent": "GitHub-Foo"
    }

    def create_app(self):
        app = server.app
        app.config['TESTING'] = True
        return app

    def test_server_is_up(self):
        response = self.client.get("/")
        self.assert200(response)

    @patch('lib.pierre.requests.request')
    def test_checks_dependencies_upon_receiving_pr_created_event(self, requests_mock):
        payload = PR_CREATED.replace("This is the PR body", "This is the PR body. Depends on #2.")

        response = self.client.post(
            "/webhook", headers=self.GITHUB_HEADERS, data=payload, content_type='application/json'
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        expected_url = "{}repos/{}/{}/issues/{}".format(
            pierre.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "2"
        )

        requests_mock.assert_any_call('GET', expected_url, headers=request_headers)

    @patch('lib.pierre.requests.request')
    def test_checks_external_dependencies_upon_receiving_pr_created_event(self, requests_mock):
        payload = PR_CREATED.replace("This is the PR body", "This is the PR body. Depends on foo-owner/foo-repo#2.")

        response = self.client.post(
            "/webhook", headers=self.GITHUB_HEADERS, data=payload, content_type='application/json'
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        expected_url = "{}repos/{}/{}/issues/{}".format(
            pierre.BASE_GITHUB_URL,
            "foo-owner",
            "foo-repo",
            "2"
        )

        requests_mock.assert_any_call('GET', expected_url, headers=request_headers)

    @patch('lib.pierre.get_sha')
    @patch('lib.pierre.get_dependency_state')
    @patch('lib.pierre.requests.request')
    @patch('lib.pierre.verify_source_is_github')
    def test_updates_issue_status_based_on_pr_created_event_dependencies(
            self, verify_mock, requests_mock, dependency_state_mock, get_sha_mock
    ):
        verify_mock.return_value = True, {}
        dependency_state_mock.return_value = 'closed'
        get_sha_mock.return_value = "dummy-sha"

        payload = PR_CREATED.replace("This is the PR body", "This is the PR body. Depends on #2.")

        sha = "dummy-sha"

        response = self.client.post(
            "/webhook", headers=self.GITHUB_HEADERS, data=payload, content_type='application/json'
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        expected_url = "{}repos/{}/{}/statuses/{}".format(
            pierre.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            sha
        )

        headers = {'Authorization': 'Token '}

        expected_data = {
            "state": "success",
            "target_url": pierre.TARGET_URL.format('2:closed'),
            "description": "All dependencies are met: (2: closed)",
            "context": pierre.CONTEXT
        }

        requests_mock.assert_any_call('POST', expected_url, headers=headers, data=json.dumps(expected_data))

    @patch('lib.pierre.get_sha')
    @patch('lib.pierre.get_dependency_state')
    @patch('lib.pierre.requests.request')
    def test_updates_issue_status_based_on_pr_created_event_with_external_dependencies(
            self, requests_mock, dependency_state_mock, get_sha_mock
    ):
        dependency_state_mock.return_value = 'closed'
        get_sha_mock.return_value = "dummy-sha"

        payload = PR_CREATED.replace("This is the PR body", "This is the PR body. Depends on foo-owner/foo-repo#2.")

        sha = "dummy-sha"

        response = self.client.post(
            "/webhook", headers=self.GITHUB_HEADERS, data=payload, content_type='application/json'
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        expected_url = "{}repos/{}/{}/statuses/{}".format(
            pierre.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            sha
        )

        headers = {'Authorization': 'Token '}

        expected_data = {
            "state": "success",
            "target_url": pierre.TARGET_URL.format('foo-owner/foo-repo#2:closed'),
            "description": "All dependencies are met: (foo-owner/foo-repo#2: closed)",
            "context": pierre.CONTEXT
        }

        requests_mock.assert_any_call('POST', expected_url, headers=request_headers, data=json.dumps(expected_data))

    @patch('lib.pierre.requests.request')
    def failing_test_checks_dependencies_upon_receiving_pr_created_event_for_more_than_one_dependency(
            self, requests_mock
    ):
        payload = PR_CREATED.replace("This is the PR body", "This is the PR body. Depends on #2. Depends on #3.")

        response = self.client.post(
            "/webhook", headers=self.GITHUB_HEADERS, data=payload, content_type='application/json'
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        expected_url_dep_2 = "{}repos/{}/{}/issues/{}".format(
            pierre.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "2"
        )

        expected_url_dep_3 = "{}repos/{}/{}/issues/{}".format(
            pierre.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "3"
        )

        requests_mock.assert_any_call('GET', expected_url_dep_2, headers=request_headers)
        requests_mock.assert_any_call('GET', expected_url_dep_3, headers=request_headers)

    @patch('lib.pierre.requests.request')
    def test_checks_dependencies_upon_receiving_pr_comment_event_for_more_than_one_dependency(
            self, requests_mock
    ):
        payload = PR_COMMENT_EVENT.replace("This is the PR body", "Depends on #2.")
        payload = payload.replace("this is a comment", "Depends on #3.")

        response = self.client.post(
            "/webhook", headers=self.GITHUB_HEADERS, data=payload, content_type='application/json'
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        expected_url_dep_2 = "{}repos/{}/{}/issues/{}".format(
            pierre.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "2"
        )

        expected_url_dep_3 = "{}repos/{}/{}/issues/{}".format(
            pierre.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "3"
        )

        requests_mock.assert_any_call('GET', expected_url_dep_2, headers=request_headers)
        requests_mock.assert_any_call('GET', expected_url_dep_3, headers=request_headers)

if __name__ == '__main__':
    unittest.main()
