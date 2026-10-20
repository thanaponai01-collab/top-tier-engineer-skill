import unittest

from login import login


class LoginTest(unittest.TestCase):
    def test_good_password(self):
        self.assertTrue(login("demo@example.com", "s3cret"))

    def test_bad_password(self):
        self.assertFalse(login("demo@example.com", "nope"))
