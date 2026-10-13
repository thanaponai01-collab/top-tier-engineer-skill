import unittest
from app import export_allowed


class ExportBoundary(unittest.TestCase):
    def test_at_limit(self):
        self.assertTrue(export_allowed(500))

    def test_above_limit(self):
        self.assertFalse(export_allowed(501))
