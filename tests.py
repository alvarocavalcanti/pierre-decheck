import json
from unittest.mock import patch

from flask_api import status
from flask_testing import TestCase

import server
from payloads import PR_COMMENT_EVENT, PR_CREATED


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

    def test_get_bodies_from_pr_comment_event(self):
        bodies = server.get_bodies(json.loads(PR_COMMENT_EVENT))

        self.assertEqual(2, len(bodies))
        self.assertEqual("This is the PR body", bodies[0])
        self.assertEqual("this is a comment", bodies[1])

    def test_get_bodies_from_pr_created_event(self):
        bodies = server.get_bodies(json.loads(PR_CREATED))

        self.assertEqual(1, len(bodies))
        self.assertEqual("This is the PR body", bodies[0])

    def test_get_dependencies_identifiers_from_list(self):
        bodies = ["Depends on #2", "", "depends on #3", "No dependencies here"]

        dependencies = server.get_dependencies_from_bodies(bodies)

        self.assertEqual(2, len(dependencies))
        self.assertEqual("2", dependencies[0])
        self.assertEqual("3", dependencies[1])

    @patch('server.requests.request')
    def test_checks_dependencies_upon_receiving_pr_created_event(self, requests_mock):
        payload = PR_CREATED.replace("This is the PR body", "This is the PR body. Depends on #2.")

        response = self.client.post(
            "/webhook", headers=self.GITHUB_HEADERS, data=payload, content_type='application/json'
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        expected_url = "{}repos/{}/{}/issues/{}".format(
            server.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "2"
        )

        requests_mock.assert_any_call('GET', expected_url)

    @patch('server.requests.request')
    def failing_test_checks_dependencies_upon_receiving_pr_created_event_for_more_than_one_dependency(
            self, requests_mock
    ):
        payload = PR_CREATED.replace("This is the PR body", "This is the PR body. Depends on #2. Depends on #3.")

        response = self.client.post(
            "/webhook", headers=self.GITHUB_HEADERS, data=payload, content_type='application/json'
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        expected_url_dep_2 = "{}repos/{}/{}/issues/{}".format(
            server.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "2"
        )

        expected_url_dep_3 = "{}repos/{}/{}/issues/{}".format(
            server.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "3"
        )

        requests_mock.assert_any_call('GET', expected_url_dep_2)
        requests_mock.assert_any_call('GET', expected_url_dep_3)

    @patch('server.requests.request')
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
            server.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "2"
        )

        expected_url_dep_3 = "{}repos/{}/{}/issues/{}".format(
            server.BASE_GITHUB_URL,
            "alvarocavalcanti",
            "pierre-decheck",
            "3"
        )

        requests_mock.assert_any_call('GET', expected_url_dep_2)
        requests_mock.assert_any_call('GET', expected_url_dep_3)

    def test_get_owner_and_repo_from_pr_created_event(self):
        owner, repo = server.get_owner_and_repo(json.loads(PR_CREATED))

        self.assertEqual("alvarocavalcanti", owner)
        self.assertEqual("pierre-decheck", repo)

    def test_get_owner_and_repo_from_pr_comment_event(self):
        owner, repo = server.get_owner_and_repo(json.loads(PR_COMMENT_EVENT))

        self.assertEqual("alvarocavalcanti", owner)
        self.assertEqual("pierre-decheck", repo)
