from flask_testing import TestCase

import server


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
