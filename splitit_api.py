import flask
import logging
import splitit
import splitit_errors

logging.basicConfig(level=logging.DEBUG)

app = flask.Flask(__name__)

@app.route('/checks')
def describe_checks():
    data = flask.request.get_json()

    return flask.jsonify(splitit.get_checks(limit=data.get('limit'), marker=data.get('marker')))

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

    check = splitit.add_location(check, data.get('name'), data.get('taxInCents'), data.get('tipInCents'))

    return flask.jsonify(check)

@app.route('/check/<check_id>/location/<location_id>', methods=['PUT'])
def update_location(check_id, location_id):
    data = flask.request.get_json()

    check = splitit.get_check(check_id)

    check = splitit.update_location(check, location_id, data.get('name'), data.get('taxInCents'), data.get('tipInCents'))

    return flask.jsonify(check)

@app.route('/check/<check_id>/location/<location_id>', methods=['DELETE'])
def remove_location(check_id, location_id):
    check = splitit.get_check(check_id)

    check = splitit.delete_location(check, location_id)

    return flask.jsonify(check)

@app.route('/check/<check_id>/line-item', methods=['POST'])
def create_line_item(check_id):
    data = flask.request.get_json()

    check = splitit.get_check(check_id)

    check = splitit.add_line_item(check, data.get('name'), data.get('locationId'), data.get('owner'), data.get('amountInCents'))

    return flask.jsonify(check)

@app.route('check/<check_id>/line-item/<line_item_id>', methods=['PUT'])
def update_line_item(check_id, line_item_id):
    data = flask.request.get_json()

    check = splitit.get_check(check_id)

    check = splitit.update_line_item(check, line_item_id, data.get('name'), data.get('locationId'), data.get('owner'), data.get('amountInCents'))

    split_ct = data.get('splitCount', 1)
    if split_ct > 1:
        check = split.split_line_item(check, line_item_id, split_ct)

    return flask.jsonify(check)

@app.route('check/<check_id>/line-item/<line_item_id>', methods=['DELETE'])
def remove_line_item(check_id, line_item_id):
    check = splitit.get_check(check_id)

    check = splitit.delete_line_item(check_id, line_item_id)

    return flask.jsonify(check)

@app.errorhandler(splitit_errors.SplititError)
def handle_splitit_error(error):
    return flask.jsonify(error.message), error.status_code
