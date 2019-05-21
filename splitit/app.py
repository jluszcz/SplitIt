from chalice import Chalice, BadRequestError, NotFoundError, ConflictError
from chalicelib import splitit

app = Chalice(app_name='splitit')
app.debug = True


@app.route('/check', methods=['POST'])
def create_check():
    request_body = app.current_request.json_body
    try:
        check = splitit.put_check(request_body.get('date'), request_body.get('description'))
    except ValueError as e:
        raise BadRequestError(e)

    return check.to_json()


def _get_check(check_id):
    check = splitit.get_check(check_id)

    if not check:
        raise NotFoundError('%s does not exist' % check_id)

    return check


@app.route('/check/{check_id}', methods=['GET'])
def get_check(check_id):
    return _get_check(check_id).to_json()


@app.route('/check/{check_id}', methods=['PUT'])
def update_check(check_id):
    request_body = app.current_request.json_body

    check = _get_check(check_id)

    try:
        check = splitit.update_check(check, request_body.get('date'), request_body.get('description'))
    except ValueError as e:
        raise BadRequestError(e)

    return check.to_json()


@app.route('/check/{check_id}', methods=['DELETE'])
def remove_check(check_id):
    check = splitit.remove_check(check_id)
    if check:
        return check.to_json()
    return {}


@app.route('/check/{check_id}/location', methods=['POST'])
def create_location(check_id):
    request_body = app.current_request.json_body

    check = _get_check(check_id)

    try:
        location = splitit.put_location(check, request_body.get('name'), request_body.get('taxInCents'),
                                        request_body.get('tipInCents'))
    except ValueError as e:
        raise BadRequestError(e)

    return location.to_json()


@app.route('/check/{check_id}/location/{location_id}', methods=['PUT'])
def update_location(check_id, location_id):
    request_body = app.current_request.json_body

    check = _get_check(check_id)

    try:
        location = splitit.update_location(check, location_id, request_body.get('name'), request_body.get('taxInCents'),
                                           request_body.get('tipInCents'))
    except ValueError as e:
        raise BadRequestError(e)
    except splitit.ConflictError as e:
        raise ConflictError(e)

    if not location:
        raise NotFoundError('No location found for %s', location_id)

    return location.to_json()


@app.route('/check/{check_id}/location/{location_id}', methods=['DELETE'])
def remove_location(check_id, location_id):
    check = _get_check(check_id)

    try:
        location = splitit.delete_location(check, location_id)
    except ValueError as e:
        raise BadRequestError(e)

    if location:
        return location.to_json()
    return {}


@app.route('/check/{check_id}/line-item', methods=['POST'])
def create_line_item(check_id):
    request_body = app.current_request.json_body

    check = _get_check(check_id)

    try:
        line_item = splitit.put_line_item(check, request_body.get('name'), request_body.get('locationId'),
                                          request_body.get('owners'), request_body.get('amountInCents'))
    except ValueError as e:
        raise BadRequestError(e)

    return line_item.to_json()


@app.route('/check/{check_id}/line-item/{line_item_id}', methods=['PUT'])
def update_line_item(check_id, line_item_id):
    request_body = app.current_request.json_body

    check = _get_check(check_id)

    try:
        line_item = splitit.update_line_item(check, line_item_id, request_body.get('name'), request_body.get('locationId'),
                                             request_body.get('ownersToAdd'), request_body.get('ownersToRemove'),
                                             request_body.get('amountInCents'))
    except ValueError as e:
        raise BadRequestError(e)
    except KeyError as e:
        raise NotFoundError(e)

    return line_item.to_json()


@app.route('/check/{check_id}/line-item/{line_item_id}', methods=['DELETE'])
def remove_line_item(check_id, line_item_id):
    """
    check = _get_check(check_id)

    line_item = splitit.delete_line_item(check_id, line_item_id)

    return flask.jsonify(line_item)
    """
    pass
