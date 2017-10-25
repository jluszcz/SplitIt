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
        self.assertEquals(tax, new_location['tax_in_cents'])
        self.assertEquals(tip, new_location['tip_in_cents'])

    def test_add_location_no_name(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_location(check, None)

    def test_add_location_bad_tax(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_location(check, 'New Location', tax_in_cents=-1)

    def test_add_location_bad_tip(self):
        check = self._create_check()

        with self.assertRaises(BadRequestError):
            splitit.add_location(check, 'New Location', tip_in_cents=-1)

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
        orig_tip = location.get('tip_in_cents')
        new_tip = 105

        check = splitit.update_location(check, orig_id, tip_in_cents=new_tip)
        location = check['locations'][-1]

        self.assertNotEquals(orig_tip, location['tip_in_cents'])
        self.assertEquals(new_tip, location['tip_in_cents'])

        check = splitit.update_location(check, orig_id)
        location = check['locations'][-1]

        self.assertIsNone(location.get('tip_in_cents'))

    def test_update_location_add_remove_tax(self):
        check = self._create_check()

        location = check['locations'][-1]

        orig_id = location['id']
        orig_tax = location.get('tax_in_cents')
        new_tax = 105

        check = splitit.update_location(check, orig_id, tax_in_cents=new_tax)
        location = check['locations'][-1]

        self.assertNotEquals(orig_tax, location['tax_in_cents'])
        self.assertEquals(new_tax, location['tax_in_cents'])

        check = splitit.update_location(check, orig_id)
        location = check['locations'][-1]

        self.assertIsNone(location.get('tax_in_cents'))

    def test_update_nonexistent_location(self):
        check = self._create_check()

        with self.assertRaises(NotFoundError):
            splitit.update_location(check, 'not-an-id')

    def test_delete_location(self):
        check = self._create_check()
        check = self._create_location(check)

        self.assertEquals(2, len(check['locations']))

        check = splitit.delete_location(check, check['locations'][-1]['id'])

        self.assertEquals(1, len(check['locations']))

    def test_delete_nonexistent_location(self):
        check = self._create_check()

        with self.assertRaises(NotFoundError):
            splitit.delete_location(check, 'not-an-id')

    def test_delete_all_locations(self):
        check = self._create_check()

        self.assertEquals(1, len(check['locations']))

        with self.assertRaises(BadRequestError):
            splitit.delete_location(check, check['locations'][-1]['id'])
