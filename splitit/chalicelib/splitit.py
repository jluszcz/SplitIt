import collections
import re

from chalicelib.model import Check, Location, LineItem

_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

_DEFAULT_QUERY_LIMIT = 25


class ConflictError(Exception):
    pass


def get_check(check_id):
    try:
        return Check.get(check_id)
    except Check.DoesNotExist:
        return None


def _validate_date(date):
    if not date or not _DATE_RE.match(date):
        raise ValueError('Invalid date: %s' % date)


def put_check(date, description):
    _validate_date(date)

    if not description:
        raise ValueError('Invalid description: %s' % description)

    check = Check()
    check.date = date
    check.description = description

    put_location(check, save=False)

    check.save()

    return check


def update_check(check, date, description):
    modified = False

    if date:
        _validate_date(date)
        check.date = date
        modified = True

    if description:
        check.description = description
        modified = True

    if modified:
        check.save()

    return check


def remove_check(check_id):
    check = get_check(check_id)

    if check:
        check.delete()

    return check


def _validate_tax_in_cents(tax_in_cents):
    if tax_in_cents and (type(tax_in_cents) != int or tax_in_cents < 0):
        raise ValueError('Invalid tax: %s' % str(tax_in_cents))


def _validate_tip_in_cents(tip_in_cents):
    if tip_in_cents and (type(tip_in_cents) != int or tip_in_cents < 0):
        raise ValueError('Invalid tip: %s' % str(tip_in_cents))


def put_location(check, location_name=None, tax_in_cents=None, tip_in_cents=None, save=True):
    _validate_tax_in_cents(tax_in_cents)
    _validate_tip_in_cents(tip_in_cents)

    for location in check.locations:
        if location.name == location_name:
            raise ValueError('A location with the name %s already exists' % location_name)

    location = Location()
    location.name = location_name

    if tax_in_cents:
        location.tax_in_cents = tax_in_cents

    if tip_in_cents:
        location.tip_in_cents = tip_in_cents

    check.locations.append(location)

    if save:
        check.save()

    return location


def update_location(check, location_id, name=None, tax_in_cents=None, tip_in_cents=None):
    _validate_tax_in_cents(tax_in_cents)
    _validate_tip_in_cents(tip_in_cents)

    location = None

    modified = False
    for loc in check.locations:
        if loc.location_id == location_id:
            if name:
                modified = True
                loc.name = name

            if tax_in_cents is not None:
                modified = True
                loc.tax_in_cents = tax_in_cents

            if tip_in_cents is not None:
                modified = True
                loc.tip_in_cents = tip_in_cents

            location = loc
            break

    if not location:
        return None

    if modified:
        check.save()

    return location


def delete_location(check, location_id):
    location = None

    locations = []
    for loc in check.locations:
        if loc.location_id == location_id:
            location = loc
            continue
        locations.append(loc)

    if not location:
        return None

    if location.line_item_count != 0:
        raise ValueError('Cannot remove location with line items')

    if not locations:
        raise ValueError('Cannot remove all locations from check: %s' % check.check_id)

    check.locations = locations
    check.save()

    return location


def _validate_amount_in_cents(amount_in_cents):
    if amount_in_cents is not None and (type(amount_in_cents) != int or amount_in_cents < 0):
        raise ValueError('Invalid amount: %s' % str(amount_in_cents))


def _validate_owners(owners):
    if owners and len(owners) != len(set(owners)):
        raise ValueError('Duplicate owners in: %s' % ', '.join(owners))


def _get_location(check, location_id):
    if not location_id:
        if len(check.locations) == 1:
            return check.locations[0]

        else:
            for location in check.locations:
                if not location.name:
                    return location
    else:
        for location in check.locations:
            if location.location_id == location_id:
                return location

    return None


def put_line_item(check, name, location_id=None, owners=None, amount_in_cents=None, save_check=True):
    if not name:
        raise ValueError('Missing name')

    location = _get_location(check, location_id)
    if not location:
        raise KeyError('Location not found')

    _validate_amount_in_cents(amount_in_cents)
    _validate_owners(owners)

    line_item = LineItem()
    line_item.name = name
    line_item.check_id = check.check_id
    line_item.location_id = location.location_id

    if amount_in_cents is not None:
        line_item.amount_in_cents = amount_in_cents

    if owners:
        line_item.owners.extend(owners)

    check.line_item_ids.append(line_item.line_item_id)

    location.line_item_count += 1

    line_item.save()

    if save_check:
        check.save()

    return line_item


def _get_line_item(check, line_item_id):
    for line_item in check.get('lineItems', []):
        if line_item_id == line_item['id']:
            return line_item
    raise KeyError('No line item found for ID: %s' % line_item_id)


def update_line_item(check, line_item_id, name=None, location_id=None, owner=None, amount_in_cents=None):
    line_item = _get_line_item(check, line_item_id)

    if name:
        line_item['name'] = name
    else:
        raise ValueError('Missing line item name')

    if location_id:
        line_item['locationId'] = location_id
    else:
        raise ValueError('Missing line item location')

    if owner:
        line_item['owner'] = owner
    else:
        line_item.pop('owner', None)

    if amount_in_cents:
        line_item['amountInCents'] = amount_in_cents
    else:
        line_item.pop('amountInCents', None)

    check.save()

    return line_item


def remove_line_item(check, line_item_id):
    line_item = None

    line_items = []
    orig_line_items = check.get('lineItems', [])
    for li in orig_line_items:
        if li['id'] == line_item_id:
            line_item = li
            continue
        line_items.append(li)

    if not line_item:
        raise KeyError('No line item found for ID: %s' % line_item_id)

    if line_items:
        check['lineItems'] = line_items
    else:
        check.pop('lineItems', None)

    check.save()

    return line_item


def group_check_by_owner(check):
    locations_by_id = {}
    for location in check['locations']:
        locations_by_id[location['id']] = location

        loc_total = 0

        for line_item in check['lineItems']:
            if location['id'] == line_item['locationId']:
                loc_total += line_item['amountInCents']

        location['tipMultiplier'] = float(location.get('tipInCents', 0)) / loc_total
        location['taxMultiplier'] = float(location.get('taxInCents', 0)) / loc_total

    by_owner = collections.Counter()

    for line_item in check['lineItems']:
        location = locations_by_id[line_item['locationId']]
        by_owner[line_item['owner']] += int(round((1 + location['tipMultiplier'] + location['taxMultiplier'])
                                                  * line_item['amountInCents']))

    return by_owner
