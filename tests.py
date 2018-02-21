import json

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
