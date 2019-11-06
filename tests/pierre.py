import logging

from flask_testing import TestCase

import server


class PierreTestCase(TestCase):
    render_templates = False

    def create_app(self):
        app = server.app
        app.config['TESTING'] = True
        return app

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        logging.disable(logging.NOTSET)
