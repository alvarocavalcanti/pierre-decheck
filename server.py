from flask import request

from flask_api import FlaskAPI, status

app = FlaskAPI(__name__)

STATUS_ERROR = 'error'
STATUS_FAILURE = 'failure'
STATUS_PENDING = 'pending'
STATUS_SUCCESS = 'success'
BASE_GITHUB_URL = 'https://api.github.com/'
KEYWORDS_DEPENDS_ON = "depends on"
CONTEXT = "continuous-integration/merge-watcher"
DESCRIPTION_PENDING = "Checking dependencies..."
DESCRIPTION_OPEN = "Dependencies are still open."
DESCRIPTION_CLOSED = "Dependencies are satisfied."


@app.route("/", methods=['GET', 'POST'])
def root_list():
    return "Pierre DeCheck: nothing to see here.", status.HTTP_200_OK


@app.route("/webhook", methods=['POST'])
def webhook_event():
    print("Received request with headers \n{} \n and data: \n{}".format(request.headers, request.data))


if __name__ == "__main__":
    app.run(debug=True)
