import json
import unittest
from unittest.mock import patch, ANY

from flask_api import status
from flask_testing import TestCase

import server
from payloads import PR_COMMENT_EVENT


class ServerTest(TestCase):
    render_templates = False

    GITHUB_HEADERS = {
        "X-GitHub-Event": "comments",
        "X-GitHub-Delivery": "foo",
        "X-Hub-Signature": "sha1=foobar"
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

    @patch('server.requests.request')
    def test_sets_pending_status_after_receiving_pull_request_comment_event(self, mock_request):
        payload = PR_COMMENT_EVENT
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


if __name__ == '__main__':
    unittest.main()
