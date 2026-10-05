import unittest
from app import answer

class TestAnswer(unittest.TestCase):
    def test_answer(self):
        self.assertEqual(answer(), 42, "expected 42")
