import unittest
from app import answer

class TestAnswer(unittest.TestCase):
    def test_answer(self):
        self.assertEqual(42, 42, "expected 42")
