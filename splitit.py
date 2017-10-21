import collections
import logging
import json

DEFAULT_LOCATION_ID = 0

def _get_check_fname(date, name):
    return 'database/%s.%s.json' % (date, name)

def _get_check(date, name):
    # TODO This should query the backing database
    try:
        with open(_get_check_fname(date, name)) as f:
            return json.loads(f.read())
    except IOError:
        logging.debug('No check found for %s - %s', date, name)
        return {}

def _save_check(check):
    # TODO This should save to the backing database
    date = check['date']
    name = check['name']

    logging.debug('Saving %s - %s', date, name)
    with open(_get_check_fname(date, name), 'w') as f:
        f.write(json.dumps(check))

def create_check(date, name):
    check = _get_check(date, name)
    if check:
        logging.warn('%s - %s already exists', date, name)
        raise ValueError('%s - %s already exists' % (date, name))

    check['name'] = name
    check['date'] = date # TODO Validate dates
    check['active'] = 1

    _save_check(check)

    return check

def get_check(date, name):
    return _get_check(date, name)

def get_check_grouped_by_owner(date, name):
    check = _get_check(date, name)
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
