import logging

from flask import request
from flask_api import FlaskAPI, status
from lib.pierre import check, update_dependants

logging.basicConfig(level=logging.INFO)

app = FlaskAPI(__name__)


@app.route("/", methods=['GET', 'POST'])
def root_list():
    return "Pierre DeCheck: nothing to see here.", status.HTTP_200_OK


@app.route("/webhook", methods=['POST'])
def webhook_event():
    app.logger.info("Received request with headers \n{}and data: \n{}".format(request.headers, request.data))
    result = check(request.data, request.headers, request.environ.get("HTTP_HOST"))

    update_dependants(request.data, request.headers, request.environ.get("HTTP_HOST"))

    return result.get("body"), result.get("statusCode")


@app.route("/details", methods=['GET'])
def details():
    info = request.args.get('info')
    dependencies_and_states = info.split('-')
    dependencies_info = [dep.replace(':', ' is ') for dep in dependencies_and_states]

    return {"dependencies": dependencies_info}, status.HTTP_200_OK


if __name__ == "__main__":
    app.run(debug=True)
