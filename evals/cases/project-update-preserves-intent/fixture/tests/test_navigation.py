import unittest
from src.auth.login import login
from src.billing.checkout import checkout

class Navigation(unittest.TestCase):
    def test_login(self):
        self.assertEqual(login('/profile'), '/profile')
    def test_checkout(self):
        self.assertEqual(checkout(), '/billing')
