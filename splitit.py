import collections
import logging
import json
import os
import re
import uuid

from splitit_errors import ConflictError, BadRequestError, NotFoundError

_DATABASE_DIR = 'database'

_DATE_RE = re.compile('^\d{4}-\d{2}-\d{2}$')

_DEFAULT_QUERY_LIMIT = 25

DEFAULT_LOCATION_NAME = 'default'

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
    if not date or not _DATE_RE.match(date):
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
    if tax_in_cents and (type(tax_in_cents) != int or tax_in_cents < 0):
        raise BadRequestError('Invalid tax: %s' % str(tax_in_cents))

def _validate_tip_in_cents(tip_in_cents):
    if tip_in_cents and (type(tip_in_cents) != int or tip_in_cents < 0):
        raise BadRequestError('Invalid tip: %s' % str(tip_in_cents))

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
        location['taxInCents'] = tax_in_cents

    if tip_in_cents:
        location['tipInCents'] = tip_in_cents

    check['locations'].append(location)
    _save_check(check)

    return location

def update_location(check, location_id, location_name=None, tax_in_cents=None, tip_in_cents=None):
    _validate_tax_in_cents(tax_in_cents)
    _validate_tip_in_cents(tip_in_cents)

    location_found = False

    for location in check['locations']:
        if location['id'] == location_id:
            if location_name:
                location['name'] = location_name

            if tax_in_cents:
                location['taxInCents'] = tax_in_cents
            else:
                location.pop('taxInCents', None)

            if tip_in_cents:
                location['tipInCents'] = tip_in_cents
            else:
                location.pop('tipInCents', None)

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

def _validate_amount_in_cents(amount_in_cents):
    if amount_in_cents and (type(amount_in_cents) != int or amount_in_cents < 0):
        raise BadRequestError('Invalid amount: %s' % str(amount_in_cents))

def _get_location(check, location_id):
    if not location_id:
        if len(check['locations']) == 1:
            return check['locations'][0]
        else:
            for location in check['locations']:
                if location['name'] == DEFAULT_LOCATION_NAME:
                    return location
    else:
        for location in check['locations']:
            if location['id'] == location_id:
                return location

    raise BadRequestError('Could not determine location')

def add_line_item(check, name, location_id=None, owner=None, amount_in_cents=None, save_check=True):
    if not name:
        raise BadRequestError('Missing line item name')

    location = _get_location(check, location_id)

    _validate_amount_in_cents(amount_in_cents)

    line_item = {
        'id': _create_id(),
        'name': name,
        'locationId': location['id'],
    }

    if amount_in_cents:
        line_item['amountInCents'] = amount_in_cents

    if owner:
        line_item['owner'] = owner

    if 'lineItems' not in check:
        check['lineItems'] = []

    check['lineItems'].append(line_item)

    if save_check:
        _save_check(check)

    return line_item

def _get_line_item(check, line_item_id):
    for line_item in check.get('lineItems', []):
        if line_item_id == line_item['id']:
            return line_item
    raise NotFoundError('No line item found for ID: %s' % line_item_id)

def update_line_item(check, line_item_id, name=None, location_id=None, owner=None, amount_in_cents=None):
    line_item = _get_line_item(check, line_item_id)

    if name:
        line_item['name'] = name
    else:
        raise BadRequestError('Missing line item name')

    if location_id:
        line_item['locationId'] = location_id
    else:
        raise BadRequestError('Missing line item location')

    if owner:
        line_item['owner'] = owner
    else:
        line_item.pop('owner', None)

    if amount_in_cents:
        line_item['amountInCents'] = amount_in_cents
    else:
        line_item.pop('amountInCents', None)

    _save_check(check)

    return check

def split_line_item(check, line_item_id, split_ct):
    if type(split_ct) != int or split_ct < 1:
        raise BadRequestError('Invalid split count: %s' % str(split_ct))

    line_item = _get_line_item(check, line_item_id)

    new_amount = int(line_item.get('amountInCents', 0) / split_ct)

    line_item['amountInCents'] = new_amount

    for n in range(split_ct - 1):
        add_line_item(check, line_item['name'], line_item['locationId'], line_item.get('owner'), new_amount, save_check=False)

    _save_check(check)

    return check

def remove_line_item(check, line_item_id):
    line_items = []
    orig_line_items = check.get('lineItems', [])
    for line_item in orig_line_items:
        if line_item['id'] == line_item_id:
            continue
        line_items.append(line_item)

    if len(line_items) == len(orig_line_items):
        raise NotFoundError('No line item found for ID: %s' % line_item_id)

    if line_items:
        check['lineItems'] = line_items
    else:
        check.pop('lineItems', None)

    _save_check(check)

    return check

def group_check_by_owner(check):
    locations_by_id = {}
    for location in check['locations']:
        locations_by_id[location['id']] = location

        loc_total = 0

        for line_item in check['lineItems']:
            loc_total += line_item['amountInCents']

        location['tipMultiplier'] = float(location.get('tipInCents', 0)) / loc_total
        location['taxMultiplier'] = float(location.get('taxInCents', 0)) / loc_total

    by_owner = collections.Counter()

    for line_item in check['lineItems']:
        location = locations_by_id[line_item['locationId']]
        by_owner[line_item['owner']] += int(round((1 + location['tipMultiplier'] + location['taxMultiplier']) * line_item['amountInCents']))

    return by_owner
