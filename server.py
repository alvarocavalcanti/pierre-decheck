from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions

app = FlaskAPI(__name__)


@app.route("/", methods=['GET', 'POST'])
def root_list():
    """
    List or create notes.
    """
    # if request.method == 'POST':
    #     note = str(request.data.get('text', ''))
    #     idx = max(notes.keys()) + 1
    #     notes[idx] = note
    #     return note_repr(idx), status.HTTP_201_CREATED

    # request.method == 'GET'
    # return [note_repr(idx) for idx in sorted(notes.keys())]
    return []


@app.route("/watch/", methods=['POST'])
def watch():
  pass

if __name__ == "__main__":
    app.run(debug=True)
