import datetime
import splitit
import unittest

class TestSplitIt(unittest.TestCase):

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

