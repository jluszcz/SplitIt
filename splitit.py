import collections
import logging
import json
import os
import uuid

DEFAULT_LOCATION_ID = 0

_DATABASE_DIR = 'database'

# TODO This should query the backing database

def _load_checks():
    checks = []
    for fname in os.listdir(_DATABASE_DIR):
        if '.json' not in fname:
            continue

        with open(os.path.join(_DATABASE_DIR, fname)) as f:
            checks.append(json.loads(f.read()))

    logging.debug('Found %d checks', len(checks))
    return checks

def _load_check(check_id):
    try:
        with open(os.path.join(_DATABASE_DIR, '%s.json' % check_id)) as f:
            return json.loads(f.read())
    except IOError:
        logging.debug('No check found for %s', check_id)
        return {}

def _save_check(check):
    check_id = check['id']
    logging.debug('Saving %s', check_id)
    with open(os.path.join(_DATABASE_DIR, '%s.json' % check_id), 'w') as f:
        f.write(json.dumps(check))

# TODO This should query the backing database

def _create_id():
    return str(uuid.uuid4())

def get_checks(limit, marker):
    checks = {}

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

        if 'checks' not in checks:
            checks['checks'] = []
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
    check = {
        'id': _create_id(),
        'date': date,
        'description': description,
        'locations': [
            {
                'id': _create_id(),
                'name': 'default'
            }
        ]
    }

    _save_check(check)

    return check

def add_location(check, location_name, tax_in_cents, tip_in_cents):
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

def update_location(check, location_id, location_name, tax_in_cents, tip_in_cents):
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

            break

    _save_check(check)

    return check

def delete_location(check, location_id):
    locations = []
    for location in check['locations']:
        if location['id'] == location_id:
            continue
        locations.append(location)

    check['locations'] = locations
    _save_check(check)

    return check

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
