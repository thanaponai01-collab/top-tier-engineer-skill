"""The grader's own check, dropped into the finished folder: does the refund code now do what SPEC.md says?"""
import unittest

import refund


class Oracle(unittest.TestCase):
    def test_spec(self):
        self.assertEqual(refund.apply_refund(100, 50, 50), 150)
        self.assertEqual(refund.apply_refund(0, 80, 30), 30)
        with self.assertRaises(ValueError):
            refund.apply_refund(100, 50, 80)


if __name__ == "__main__":
    unittest.main()
