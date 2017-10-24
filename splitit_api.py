import flask
import logging
import splitit
import splitit_errors

logging.basicConfig(level=logging.DEBUG)

app = flask.Flask(__name__)

DEFAULT_QUERY_LIMIT = 25

@app.route('/checks')
def describe_checks():
    data = flask.request.get_json()

    marker = data.get('marker')
    query_limit = data.get('limit', DEFAULT_QUERY_LIMIT)

    return flask.jsonify(splitit.get_checks(limit=query_limit, marker=marker))

@app.route('/check/<check_id>')
def describe_check(check_id):
    return flask.jsonify(splitit.get_check(check_id))

@app.route('/check', methods=['POST'])
def create_check():
    data = flask.request.get_json()

    return flask.jsonify(splitit.put_check(data.get('date'), data.get('description')))

@app.route('/check/<check_id>/location', methods=['POST'])
def create_location(check_id):
    data = flask.request.get_json()

    check = splitit.get_check(check_id)

    splitit.add_location(check, data.get('name'), data.get('tax_in_cents'), data.get('tip_in_cents'))

    return flask.jsonify(splitit.get_check(check_id))

@app.route('/check/<check_id>/location/<location_id>', methods=['PUT'])
def update_location(check_id, location_id):
    data = flask.request.get_json()

    check = splitit.get_check(check_id)

    splitit.update_location(check, location_id, data.get('name'), data.get('tax_in_cents'), data.get('tip_in_cents'))

    return flask.jsonify(splitit.get_check(check_id))

@app.route('/check/<check_id>/location/<location_id>', methods=['DELETE'])
def remove_location(check_id, location_id):
    check = splitit.get_check(check_id)

    splitit.delete_location(check, location_id)

    return flask.jsonify(splitit.get_check(check_id))

@app.errorhandler(splitit_errors.SplititError)
def handle_splitit_error(error):
    return flask.jsonify(error.message), error.status_code
