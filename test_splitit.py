import copy
import datetime
import splitit
import unittest

from splitit_errors import BadRequestError, ConflictError, NotFoundError

class TestSplitIt(unittest.TestCase):

    def setUp(self):
        self.checks_to_remove = []

    def tearDown(self):
        for check in self.checks_to_remove:
            try:
                splitit.remove_check(check)
            except NotFoundError:
                pass

    def _create_check(self):
        check = splitit.put_check(datetime.date.today().isoformat(), 'Test Check')
        self.checks_to_remove.append(check['id'])
        return check

    def _create_location(self, check, tax_in_cents=None, tip_in_cents=None):
        loc_num = len(check['locations'])
        check = splitit.add_location(check, 'Location %d' % loc_num, tax_in_cents=tax_in_cents, tip_in_cents=tip_in_cents)
        return check

    def test_put_get_check(self):
        date = datetime.date.today().isoformat()
        desc = 'Test Check'

        new_check = splitit.put_check(date, desc)

        self.checks_to_remove.append(new_check['id'])

        self.assertIsNotNone(new_check.get('id'))
        self.assertEquals(date, new_check['date'])
        self.assertEquals(desc, new_check['description'])

        locations = new_check['locations']

        self.assertEquals(1, len(locations))

        location = locations[-1]
        self.assertIsNotNone(location.get('id'))
        self.assertEquals(splitit.DEFAULT_LOCATION_NAME, location['name'])

        retrieved_check = splitit.get_check(new_check['id'])
        self.assertEquals(new_check, retrieved_check)

    def test_put_check_no_date(self):
        with self.assertRaises(BadRequestError):
            splitit.put_check(None, 'Test Check')

    def test_put_check_bad_date(self):
        with self.assertRaises(BadRequestError):
            splitit.put_check('Not a Date', 'Test Check')

    def test_put_check_no_description(self):
        with self.assertRaises(BadRequestError):
            splitit.put_check(datetime.date.today().isoformat(), None)

    def test_get_checks(self):
        check_ids = []

        no_pagination_ct = 10

        assert no_pagination_ct < splitit._DEFAULT_QUERY_LIMIT / 2

        for n in range(no_pagination_ct):
            check_ids.append(self._create_check()['id'])

        checks = splitit.get_checks()

        self.assertIsNone(checks.get('marker'))

        returned_ids = [c['id'] for c in checks['checks']]

        for check_id in check_ids:
            self.assertTrue(check_id in returned_ids)

    def test_get_checks_pagination(self):
        check_ids = []

        for n in range(10):
            check_ids.append(self._create_check()['id'])

        limit = 2

        returned_ids = []

        queries = 0

        marker = None
        while True:
            checks = splitit.get_checks(limit=limit, marker=marker)

            queries += 1
            self.assertTrue(len(checks['checks']) <= limit)

            returned_ids += [c['id'] for c in checks['checks']]

            marker = checks.get('marker')
            if not marker:
                break

        self.assertTrue(queries >= len(check_ids) / limit)

        for check_id in check_ids:
            self.assertTrue(check_id in returned_ids)

    def test_add_location(self):
        check = self._create_check()

        locations = check['locations']
        self.assertEquals(1, len(locations))

        loc_name = 'New Location'
        tax = 105
        tip = 210
        check = splitit.add_location(check, 'New Location', tax_in_cents=tax, tip_in_cents=tip)

        locations = check['locations']
        self.assertEquals(2, len(locations))

        new_location = locations[-1]
        self.assertEquals(loc_name, new_location['name'])
        self.assertEquals(tax, new_location['taxInCents'])
        self.assertEquals(tip, new_location['tipInCents'])

    def test_add_location_no_name(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_location(check, None)

    def test_add_location_bad_tax_1(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_location(check, 'New Location', tax_in_cents=-1)

    def test_add_location_bad_tax_2(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_location(check, 'New Location', tax_in_cents='not a number')

    def test_add_location_bad_tip_1(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_location(check, 'New Location', tip_in_cents=-1)

    def test_add_location_bad_tip_2(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_location(check, 'New Location', tip_in_cents='not a number')

    def test_add_location_with_conflicting_name(self):
        check = self._create_check()

        with self.assertRaises(ConflictError):
            splitit.add_location(check, splitit.DEFAULT_LOCATION_NAME)

    def test_update_location_name(self):
        check = self._create_check()

        location = check['locations'][-1]

        orig_id = location['id']
        orig_name = location['name']
        new_name = orig_name + ' Updated'

        check = splitit.update_location(check, orig_id, location_name=new_name)
        location = check['locations'][-1]

        self.assertEquals(orig_id, location['id'])
        self.assertNotEquals(orig_name, location['name'])
        self.assertEquals(new_name, location['name'])

    def test_update_location_add_remove_tip(self):
        check = self._create_check()

        location = check['locations'][-1]

        orig_id = location['id']
        orig_tip = location.get('tipInCents')
        new_tip = 105

        check = splitit.update_location(check, orig_id, tip_in_cents=new_tip)
        location = check['locations'][-1]

        self.assertNotEquals(orig_tip, location['tipInCents'])
        self.assertEquals(new_tip, location['tipInCents'])

        check = splitit.update_location(check, orig_id)
        location = check['locations'][-1]

        self.assertIsNone(location.get('tip_in_cents'))

    def test_update_location_add_remove_tax(self):
        check = self._create_check()

        location = check['locations'][-1]

        orig_id = location['id']
        orig_tax = location.get('taxInCents')
        new_tax = 105

        check = splitit.update_location(check, orig_id, tax_in_cents=new_tax)
        location = check['locations'][-1]

        self.assertNotEquals(orig_tax, location['taxInCents'])
        self.assertEquals(new_tax, location['taxInCents'])

        check = splitit.update_location(check, orig_id)
        location = check['locations'][-1]

        self.assertIsNone(location.get('tax_in_cents'))

    def test_update_location_not_found(self):
        check = self._create_check()

        with self.assertRaises(NotFoundError):
            splitit.update_location(check, 'bad_id')

    def test_delete_location(self):
        check = self._create_check()
        check = self._create_location(check)

        self.assertEquals(2, len(check['locations']))

        check = splitit.delete_location(check, check['locations'][-1]['id'])

        self.assertEquals(1, len(check['locations']))

    def test_delete_location_not_found(self):
        check = self._create_check()

        with self.assertRaises(NotFoundError):
            splitit.delete_location(check, 'bad_id')

    def test_delete_all_locations(self):
        check = self._create_check()

        self.assertEquals(1, len(check['locations']))

        with self.assertRaises(BadRequestError):
            splitit.delete_location(check, check['locations'][-1]['id'])

    def test_add_line_item_to_default_location(self):
        check = self._create_check()
        check = self._create_location(check)

        for location in check['locations']:
            if location['name'] == splitit.DEFAULT_LOCATION_NAME:
                location_id = location['id']

        self.assertFalse('lineItems' in check)

        line_item_name = 'Food'
        line_item_owner = 'John Doe'
        line_item_amt = 105

        check = splitit.add_line_item(check, name=line_item_name, owner=line_item_owner, amount_in_cents=line_item_amt)

        self.assertEquals(1, len(check['lineItems']))

        line_item = check['lineItems'][-1]

        self.assertEquals(location_id, line_item['locationId'])
        self.assertEquals(line_item_name, line_item['name'])
        self.assertEquals(line_item_owner, line_item['owner'])
        self.assertEquals(line_item_amt, line_item['amountInCents'])

    def test_add_line_item_to_non_default_location(self):
        check = self._create_check()
        check = self._create_location(check)

        for location in check['locations']:
            if location['name'] != splitit.DEFAULT_LOCATION_NAME:
                location_id = location['id']

        self.assertFalse('lineItems' in check)

        line_item_name = 'Food'
        line_item_owner = 'John Doe'
        line_item_amt = 105

        check = splitit.add_line_item(check, name=line_item_name, location_id=location_id, owner=line_item_owner, amount_in_cents=line_item_amt)

        self.assertEquals(1, len(check['lineItems']))

        line_item = check['lineItems'][-1]

        self.assertEquals(location_id, line_item['locationId'])
        self.assertEquals(line_item_name, line_item['name'])
        self.assertEquals(line_item_owner, line_item['owner'])
        self.assertEquals(line_item_amt, line_item['amountInCents'])

    def test_add_line_item_to_only_non_default_location(self):
        check = self._create_check()
        check = self._create_location(check)

        for location in check['locations']:
            if location['name'] == splitit.DEFAULT_LOCATION_NAME:
                default_location_id = location['id']
            else:
                location_id = location['id']

        check = splitit.delete_location(check, default_location_id)

        self.assertFalse('lineItems' in check)

        line_item_name = 'Food'
        line_item_owner = 'John Doe'
        line_item_amt = 105

        check = splitit.add_line_item(check, name=line_item_name, owner=line_item_owner, amount_in_cents=line_item_amt)

        self.assertEquals(1, len(check['lineItems']))

        line_item = check['lineItems'][-1]

        self.assertEquals(location_id, line_item['locationId'])
        self.assertEquals(line_item_name, line_item['name'])
        self.assertEquals(line_item_owner, line_item['owner'])
        self.assertEquals(line_item_amt, line_item['amountInCents'])

    def test_add_line_item_no_name(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_line_item(check, name=None)

    def test_add_line_item_bad_amount_1(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_line_item(check, 'Food', amount_in_cents=-1)

    def test_add_line_item_bad_amount_2(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_line_item(check, 'Food', amount_in_cents='not a number')

    def test_update_line_item_name(self):
        check = self._create_check()

        name = 'Food'
        check = splitit.add_line_item(check, name)

        orig_li = copy.deepcopy(check['lineItems'][-1])

        new_name = 'Not Food'
        check = splitit.update_line_item(check, orig_li['id'], new_name, orig_li['locationId'])

        li = check['lineItems'][-1]

        self.assertEquals(new_name, li['name'])
        self.assertEquals(orig_li['id'], li['id'])
        self.assertEquals(orig_li['locationId'], li['locationId'])

    def test_update_line_item_add_remove_owner(self):
        check = self._create_check()

        check = splitit.add_line_item(check, 'Food', owner='Owner')

        orig_li = copy.deepcopy(check['lineItems'][-1])

        new_owner = 'New Owner'

        check = splitit.update_line_item(check, orig_li['id'], orig_li['name'], orig_li['locationId'], owner=new_owner)

        li = check['lineItems'][-1]

        self.assertEquals(orig_li['id'], li['id'])
        self.assertEquals(new_owner, li['owner'])

        check = splitit.update_line_item(check, orig_li['id'], orig_li['name'], orig_li['locationId'], owner=None)

        li = check['lineItems'][-1]

        self.assertEquals(orig_li['id'], li['id'])
        self.assertIsNone(li.get('owner'))

    def test_update_line_item_add_remove_amount(self):
        check = self._create_check()

        check = splitit.add_line_item(check, 'Food', amount_in_cents=105)

        orig_li = copy.deepcopy(check['lineItems'][-1])

        new_amt = 30

        check = splitit.update_line_item(check, orig_li['id'], orig_li['name'], orig_li['locationId'], amount_in_cents=new_amt)

        li = check['lineItems'][-1]

        self.assertEquals(orig_li['id'], li['id'])
        self.assertEquals(new_amt, li['amountInCents'])

        check = splitit.update_line_item(check, orig_li['id'], orig_li['name'], orig_li['locationId'], amount_in_cents=None)

        li = check['lineItems'][-1]

        self.assertEquals(orig_li['id'], li['id'])
        self.assertIsNone(li.get('amountInCents'))

    def test_update_line_item_not_found(self):
        check = self._create_check()

        with self.assertRaises(NotFoundError):
            splitit.update_line_item(check, 'bad_id')

    def test_update_line_item_no_name(self):
        check = self._create_check()

        check = splitit.add_line_item(check, 'Food')

        li = check['lineItems'][-1]

        with self.assertRaises(BadRequestError):
            splitit.update_line_item(check, li['id'], name=None, location_id=li['locationId'])

    def test_update_line_item_no_location(self):
        check = self._create_check()

        check = splitit.add_line_item(check, 'Food')

        li = check['lineItems'][-1]

        with self.assertRaises(BadRequestError):
            splitit.update_line_item(check, li['id'], name=li['name'], location_id=None)

    def test_remove_line_item(self):
        check = self._create_check()

        check = splitit.add_line_item(check, 'Food')
        check = splitit.add_line_item(check, 'Drink')

        self.assertEquals(2, len(check['lineItems']))

        li = check['lineItems'][-1]

        check = splitit.remove_line_item(check, li['id'])

        self.assertEquals(1, len(check['lineItems']))

        for l in check['lineItems']:
            self.assertNotEquals(li['id'], l['id'])

    def test_remove_only_line_item(self):
        check = self._create_check()

        check = splitit.add_line_item(check, 'Food')

        li = check['lineItems'][-1]

        check = splitit.remove_line_item(check, li['id'])

        self.assertIsNone(check.get('lineItems'))

    def test_remove_line_item_not_found(self):
        check = self._create_check()

        with self.assertRaises(NotFoundError):
            splitit.remove_line_item(check, 'bad_id')

    def test_split_line_item(self):
        check = self._create_check()

        line_item_name = 'Food'
        line_item_owner = 'John Doe'
        line_item_amt = 200

        check = splitit.add_line_item(check, name=line_item_name, owner=line_item_owner, amount_in_cents=line_item_amt)

        self.assertEquals(1, len(check['lineItems']))

        line_item = copy.deepcopy(check['lineItems'][-1])

        check = splitit.split_line_item(check, line_item['id'], 1)

        self.assertEquals(1, len(check['lineItems']))

        updated_line_item = check['lineItems'][-1]

        self.assertEquals(line_item['id'], updated_line_item['id'])
        self.assertEquals(line_item['locationId'], updated_line_item['locationId'])
        self.assertEquals(line_item['name'], updated_line_item['name'])
        self.assertEquals(line_item['owner'], updated_line_item['owner'])
        self.assertEquals(line_item['amountInCents'], updated_line_item['amountInCents'])

        split_ct = 3
        check = splitit.split_line_item(check, line_item['id'], split_ct)

        self.assertEquals(split_ct, len(check['lineItems']))

        found_orig = False
        not_orig_ct = 0

        for li in check['lineItems']:
            if line_item['id'] == li['id']:
                found_orig = True
            else:
                not_orig_ct += 1

            self.assertEquals(line_item['name'], updated_line_item['name'])
            self.assertEquals(line_item['owner'], updated_line_item['owner'])
            self.assertEquals(line_item['amountInCents'] / split_ct, updated_line_item['amountInCents'])

        self.assertTrue(found_orig)
        self.assertEquals(split_ct - 1, not_orig_ct)

    def test_split_line_item_bad_count_1(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.split_line_item(check, 'id', 0)

    def test_split_line_item_bad_count_2(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.split_line_item(check, 'id', '0')