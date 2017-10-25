import collections
import logging
import json
import os
import re
import uuid

from splitit_errors import ConflictError, BadRequestError, NotFoundError

_DATABASE_DIR = 'database'

DATE_RE = re.compile('^\d{4}-\d{2}-\d{2}$')

DEFAULT_LOCATION_NAME = 'default'

_DEFAULT_QUERY_LIMIT = 25

# TODO This should query the backing database

def _load_checks():
    checks = []
    for fname in os.listdir(_DATABASE_DIR):
        if '.json' not in fname:
            continue

        with open(os.path.join(_DATABASE_DIR, fname)) as f:
            checks.append(json.loads(f.read()))

    logging.debug('Found %d checks', len(checks))

    return sorted(checks, key=lambda c: c.get('id'))

def _load_check(check_id):
    try:
        with open(os.path.join(_DATABASE_DIR, '%s.json' % check_id)) as f:
            return json.loads(f.read())
    except IOError:
        raise NotFoundError('No check found for ID: %s' % check_id)

def _save_check(check):
    check_id = check['id']
    logging.debug('Saving %s', check_id)
    with open(os.path.join(_DATABASE_DIR, '%s.json' % check_id), 'w') as f:
        f.write(json.dumps(check))

def _delete_check(check_id):
    fname = os.path.join(_DATABASE_DIR, '%s.json' % check_id)
    if os.path.exists(fname):
        os.remove(fname)
    else:
        raise NotFoundError('No check found for ID: %s' % check_id)

# TODO This should query the backing database

def _create_id():
    return str(uuid.uuid4())

def get_checks(limit=None, marker=None):

    limit = limit or _DEFAULT_QUERY_LIMIT

    checks = {
        'checks': []
    }

    next_marker = None
    hit_limit = False

    for check in _load_checks():
        next_marker = check['id']

        if next_marker <= marker:
            continue

        check_desc = {
            'id': check['id'],
            'description': check['description'],
            'date': check['date']
        }

        checks['checks'].append(check_desc)

        if len(checks['checks']) == limit:
            hit_limit = True
            break

    if hit_limit:
        checks['marker'] = next_marker

    return checks

def get_check(check_id):
    return _load_check(check_id)

def put_check(date, description):
    if not date or not DATE_RE.match(date):
        raise BadRequestError('Invalid date: %s' % date)

    if not description:
        raise BadRequestError('Invalid description: %s' % description)

    check = {
        'id': _create_id(),
        'date': date,
        'description': description,
        'locations': []
    }

    add_location(check, DEFAULT_LOCATION_NAME)

    _save_check(check)

    return check

def remove_check(check_id):
    _delete_check(check_id)

def _validate_tax_in_cents(tax_in_cents):
    if tax_in_cents and tax_in_cents < 0:
        raise BadRequestError('Invalid tax_in_cents: %d' % tax_in_cents)

def _validate_tip_in_cents(tip_in_cents):
    if tip_in_cents and tip_in_cents < 0:
        raise BadRequestError('Invalid tip_in_cents: %d' % tip_in_cents)

def add_location(check, location_name, tax_in_cents=None, tip_in_cents=None):
    if not location_name:
        raise BadRequestError('Missing location name')
    _validate_tax_in_cents(tax_in_cents)
    _validate_tip_in_cents(tip_in_cents)

    for location in check['locations']:
        if location['name'] == location_name:
            raise ConflictError('A location with the name %s already exists' % location_name)

    location = {
        'id': _create_id(),
        'name': location_name
    }

    if tax_in_cents:
        location['tax_in_cents'] = tax_in_cents

    if tip_in_cents:
        location['tip_in_cents'] = tip_in_cents

    check['locations'].append(location)
    _save_check(check)

    return check

def update_location(check, location_id, location_name=None, tax_in_cents=None, tip_in_cents=None):
    _validate_tax_in_cents(tax_in_cents)
    _validate_tip_in_cents(tip_in_cents)

    location_found = False

    for location in check['locations']:
        if location['id'] == location_id:
            if location_name:
                location['name'] = location_name

            if tax_in_cents:
                location['tax_in_cents'] = tax_in_cents
            else:
                location.pop('tax_in_cents', None)

            if tip_in_cents:
                location['tip_in_cents'] = tip_in_cents
            else:
                location.pop('tip_in_cents', None)

            location_found = True
            break

    if not location_found:
        raise NotFoundError('No location found for ID: %s' % location_id)

    _save_check(check)

    return check

def delete_location(check, location_id):
    locations = []
    for location in check['locations']:
        if location['id'] == location_id:
            continue
        locations.append(location)

    if len(locations) == len(check['locations']):
        raise NotFoundError('No location found for ID: %s' % location_id)

    if not locations:
        raise BadRequestError('Cannot remove all locations from check: %s' % check['id'])

    check['locations'] = locations
    _save_check(check)

    return check

# TODO This was implemented for a past model version, needs updating
def get_check_grouped_by_owner(date, name):
    check = _load_check(date, name)
    if not check:
        return {}

    locations_by_id = {}
    for location in check['locations']:
        loc_id = location['id']

        locations_by_id[loc_id] = location

        loc_total = 0

        for line_item in check['line_items']:
            if loc_id != line_item.get('location_id', DEFAULT_LOCATION_ID):
                continue

            loc_total += line_item['amount']

        location['tip_multiplier'] = float(location['tip']) / loc_total
        location['tax_multiplier'] = float(location['tax']) / loc_total

    by_owner = collections.Counter()

    for line_item in check['line_items']:
        location = locations_by_id[line_item.get('location_id', DEFAULT_LOCATION_ID)]
        by_owner[line_item['owner']] += int(round((1 + location['tip_multiplier'] + location['tax_multiplier']) * line_item['amount']))

    return by_owner
