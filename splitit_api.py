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

@app.route('/checks/<date>/<name>', methods=['PUT'])
def create_check(date, name):
    try:
        return flask.jsonify(splitit.create_check(date, name))
    except ValueError:
        flask.abort(409)

@app.route('/checks/<date>/<name>/locations')
def get_check_locations(date, name):
    check = splitit.get_check(date, name)
    if not check:
        flask.abort(404)
    return flask.jsonify(check.get('locations', []))

@app.route('/checks/<date>/<name>/location/<location>', methods=['POST'])
def update_location(date, name, location=None):
    data = flask.request.get_json()
    loc_data = splitit.update_location(date, name, location, data)
    return flask.jsonify(loc_data or [])

@app.route('/checks/<date>/<name>/by_owner')
def get_amounts_by_owner(date, name):
    amounts = splitit.get_check_grouped_by_owner(date, name)
    if not amounts:
        flask.abort(404)
    return flask.jsonify(amounts)
