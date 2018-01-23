import json
import unittest
from unittest.mock import patch, ANY

from flask_api import status
from flask_testing import TestCase

import server
from payloads import PR_COMMENT_EVENT


class ServerTest(TestCase):
    render_templates = False

    def create_app(self):
        app = server.app
        app.config['TESTING'] = True
        return app

    def test_server_is_up(self):
        response = self.client.get("/")
        self.assert200(response)

    def test_consumes_pull_request_comment_event(self):
        payload = PR_COMMENT_EVENT
        response = self.client.post("/prcomment", data=payload)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    @patch('server.requests.request')
    def test_sets_pending_status_after_receiving_pull_request_comment_event(self, mock_request):
        payload = PR_COMMENT_EVENT
        headers = {
            "Content-Type": "application/json"
        }
        response = self.client.post("/prcomment", headers=headers, data=payload)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        expected_data = {
            "state": "pending",
            "target_url": "foo",
            "description": "Checking dependencies...",
            "context": "continuous-integration/merge-watcher"
        }

        mock_request.assert_called_once_with('POST', ANY, data=json.dumps(expected_data))


if __name__ == '__main__':
    unittest.main()
