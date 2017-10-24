import datetime
import splitit
import unittest

from splitit_errors import BadRequestError, ConflictError, NotFoundError

class TestSplitIt(unittest.TestCase):

    def _create_check(self):
        return splitit.put_check(datetime.date.today().isoformat(), 'Test Check')

    def test_put_get_check(self):
        date = datetime.date.today().isoformat()
        desc = 'Test Check'

        new_check = splitit.put_check(date, desc)

        self.assertIsNotNone(new_check.get('id'))
        self.assertEquals(date, new_check['date'])
        self.assertEquals(desc, new_check['description'])

        locations = new_check['locations']

        self.assertEquals(1, len(locations))

        location = locations[0]
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

    def test_add_location(self):
        check = self._create_check()

        locations = check['locations']
        self.assertEquals(1, len(locations))

        loc_name = 'New Location'
        check = splitit.add_location(check, loc_name)

        locations = check['locations']
        self.assertEquals(2, len(locations))

    def test_add_location_with_conflicting_name(self):
        check = self._create_check()

        with self.assertRaises(ConflictError):
            splitit.add_location(check, splitit.DEFAULT_LOCATION_NAME)

