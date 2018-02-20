import json
import unittest
from collections import namedtuple
from unittest.mock import patch, ANY

from flask_api import status
from flask_testing import TestCase

import server_old as server
from payloads import PR_COMMENT_EVENT, ISSUE_RESPONSE_OPEN


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

    def test_consumes_pull_request_comment_event(self):
        payload = PR_COMMENT_EVENT
        response = self.client.post("/prcomment", headers=self.GITHUB_HEADERS, data=payload)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_accepts_proper_issued_pull_request_comment_event(self):
        payload = PR_COMMENT_EVENT
        response = self.client.post("/prcomment", headers=self.GITHUB_HEADERS, data=payload)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_does_not_accept_request_without_headers_for_pull_request_comment_event(self):
        payload = PR_COMMENT_EVENT
        response = self.client.post("/prcomment", data=payload)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_does_not_accept_get_method_for_pull_request_comment_event(self):
        payload = PR_COMMENT_EVENT
        response = self.client.get("/prcomment", headers=self.GITHUB_HEADERS, data=payload)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)

    @patch('server.check_dependency')
    @patch('server.requests.request')
    def test_does_nothing_when_comment_event_does_not_have_keywords(self, mock_request, mock_check_dependecy):
        payload = PR_COMMENT_EVENT
        headers = {
            "Content-Type": "application/json"
        }

        headers.update(self.GITHUB_HEADERS)
        response = self.client.post("/prcomment", headers=headers, data=payload)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        mock_request.assert_not_called()
        mock_check_dependecy.assert_not_called()

    @patch('server.check_dependency')
    @patch('server.requests.request')
    def test_checks_pull_request_dependency_if_comment_event_has_keywords_and_updates_commit_status(
            self, mock_request, mock_check_dependency
    ):
        mock_check_dependency.return_value = "closed"
        payload = PR_COMMENT_EVENT
        payload = payload.replace("COMMENT_BODY", "Depends on #2")
        headers = {
            "Content-Type": "application/json"
        }

        headers.update(self.GITHUB_HEADERS)
        response = self.client.post("/prcomment", headers=headers, data=payload)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.data)

        expected_data = {
            "state": "pending",
            "target_url": "foo",
            "description": "Checking dependencies...",
            "context": "continuous-integration/merge-watcher"
        }

        mock_request.assert_any_call('POST', ANY, data=json.dumps(expected_data))

        expected_data.update({
            "state": "success",
            "description": "Dependencies are satisfied."
        })

        print("CALLS: {}".format(mock_request.call_args_list))
        mock_request.assert_any_call('POST', ANY, data=json.dumps(expected_data))

        mock_check_dependency.assert_called_once_with("2", "baxterthehacker", "public-repo")

    @patch('server.requests.request')
    def test_set_status_as_error(self, mock_request):
        server.set_status(
            owner='john',
            repo='johnsrepo',
            sha='johnscommit',
            commit_status='error',
            description='desc'
        )

        url = '{}repos/john/johnsrepo/statuses/johnscommit'.format(server.BASE_GITHUB_URL)
        expected_data = {
            "state": "error",
            "target_url": "foo",
            "description": "desc",
            "context": "continuous-integration/merge-watcher"
        }

        mock_request.assert_called_once_with('POST', url, data=json.dumps(expected_data))

    @patch('server.requests.request')
    def test_set_status_as_failure(self, mock_request):
        server.set_status(
            owner='john',
            repo='johnsrepo',
            sha='johnscommit',
            commit_status='failure',
            description='desc'
        )

        url = '{}repos/john/johnsrepo/statuses/johnscommit'.format(server.BASE_GITHUB_URL)
        expected_data = {
            "state": "failure",
            "target_url": "foo",
            "description": "desc",
            "context": "continuous-integration/merge-watcher"
        }

        mock_request.assert_called_once_with('POST', url, data=json.dumps(expected_data))

    @patch('server.requests.request')
    def test_set_status_as_pending(self, mock_request):
        server.set_status(
            owner='john',
            repo='johnsrepo',
            sha='johnscommit',
            commit_status='pending',
            description='desc'
        )

        url = '{}repos/john/johnsrepo/statuses/johnscommit'.format(server.BASE_GITHUB_URL)
        expected_data = {
            "state": "pending",
            "target_url": "foo",
            "description": "desc",
            "context": "continuous-integration/merge-watcher"
        }

        mock_request.assert_called_once_with('POST', url, data=json.dumps(expected_data))

    @patch('server.requests.request')
    def test_set_status_as_success(self, mock_request):
        server.set_status(
            owner='john',
            repo='johnsrepo',
            sha='johnscommit',
            commit_status='success',
            description='desc'
        )

        url = '{}repos/john/johnsrepo/statuses/johnscommit'.format(server.BASE_GITHUB_URL)
        expected_data = {
            "state": "success",
            "target_url": "foo",
            "description": "desc",
            "context": "continuous-integration/merge-watcher"
        }

        mock_request.assert_called_once_with('POST', url, data=json.dumps(expected_data))

    @patch('server.requests.request')
    def test_checks_dependency_properly(self, mock_request):
        server.check_dependency("1", "foo-owner", "foo-repo")

        expected_url = "{}repos/{}/{}/issues/{}".format(
            server.BASE_GITHUB_URL,
            "foo-owner",
            "foo-repo",
            "1"
        )

        mock_request.assert_called_once_with('GET', expected_url)

    @patch('server.requests.request')
    def test_returns_dependency_status(self, mock_request):
        Response = namedtuple('Response', ['status_code', 'text'])
        mock_request.return_value = Response(status_code=status.HTTP_200_OK, text=ISSUE_RESPONSE_OPEN)

        issue_state = server.check_dependency("1", "foo-owner", "foo-repo")

        self.assertEqual("open", issue_state)

    @patch('server.requests.request')
    def test_set_original_commit_status_as_failure_when_dependency_state_is_open(self, mock_request):
        dependency_state = "open"
        owner = "foo-owner"
        repo = "foo-repo"
        sha = "12309f"

        server.update_commit_status(owner, repo, sha, dependency_state)

        expected_url = "{}repos/{}/{}/statuses/{}".format(
            server.BASE_GITHUB_URL,
            owner,
            repo,
            sha
        )

        expected_data = {
            "state": "failure",
            "target_url": "foo",
            "description": "Dependencies are still open.",
            "context": server.CONTEXT
        }
        mock_request.assert_called_once_with('POST', expected_url, data=json.dumps(expected_data))

    @patch('server.requests.request')
    def test_set_original_commit_status_as_success_when_dependency_state_is_closed(self, mock_request):
        dependency_state = "closed"
        owner = "foo-owner"
        repo = "foo-repo"
        sha = "12309f"

        server.update_commit_status(owner, repo, sha, dependency_state)

        expected_url = "{}repos/{}/{}/statuses/{}".format(
            server.BASE_GITHUB_URL,
            owner,
            repo,
            sha
        )

        expected_data = {
            "state": "success",
            "target_url": "foo",
            "description": "Dependencies are satisfied.",
            "context": server.CONTEXT
        }
        mock_request.assert_called_once_with('POST', expected_url, data=json.dumps(expected_data))

    @patch('server.requests.request')
    def test_set_original_commit_status_as_pending_when_dependency_state_is_unknown(self, mock_request):
        dependency_state = None
        owner = "foo-owner"
        repo = "foo-repo"
        sha = "12309f"

        server.update_commit_status(owner, repo, sha, dependency_state)

        expected_url = "{}repos/{}/{}/statuses/{}".format(
            server.BASE_GITHUB_URL,
            owner,
            repo,
            sha
        )

        expected_data = {
            "state": "pending",
            "target_url": "foo",
            "description": "Checking dependencies...",
            "context": server.CONTEXT
        }
        mock_request.assert_called_once_with('POST', expected_url, data=json.dumps(expected_data))

    @patch('server.update_commit_status')
    @patch('server.check_dependency')
    @patch('server.requests.request')
    def test_update_commit_status_when_pr_comment_is_accepted(self,
                                                              mock_request,
                                                              mock_check_dependency,
                                                              mock_update_commit_status
                                                              ):
        mock_check_dependency.return_value = "open"

        payload = PR_COMMENT_EVENT
        payload = payload.replace("COMMENT_BODY", "Depends on #2")
        headers = {
            "Content-Type": "application/json"
        }

        headers.update(self.GITHUB_HEADERS)
        response = self.client.post("/prcomment", headers=headers, data=payload)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.data)

        expected_data = {
            "state": "pending",
            "target_url": "foo",
            "description": "Checking dependencies...",
            "context": "continuous-integration/merge-watcher"
        }

        mock_request.assert_called_once_with('POST', ANY, data=json.dumps(expected_data))
        mock_check_dependency.assert_called_once_with("2", "baxterthehacker", "public-repo")
        mock_update_commit_status.assert_called_once_with(
            "baxterthehacker", "public-repo", "0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c", "open"
        )


if __name__ == '__main__':
    unittest.main()
