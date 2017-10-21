import flask
import logging
import splitit

logging.basicConfig(level=logging.DEBUG)

app = flask.Flask(__name__)

@app.route('/checks/<date>/<name>')
def get_check(date, name):
    check = splitit.get_check(date, name)
    if not check:
        flask.abort(404)
    return flask.jsonify(check)

@app.route('/checks/<date>/<name>/by_owner')
def get_amounts_by_owner(date, name):
    amounts = splitit.get_check_grouped_by_owner(date, name)
    if not amounts:
        flask.abort(404)
    return flask.jsonify(amounts)
