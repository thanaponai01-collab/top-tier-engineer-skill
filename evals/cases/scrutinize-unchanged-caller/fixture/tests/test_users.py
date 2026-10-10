import unittest
from users import get_user


class GetUser(unittest.TestCase):
    def test_known(self):
        self.assertEqual(get_user("u1")["name"], "Ada")

    def test_unknown_is_none(self):
        self.assertIsNone(get_user("nobody"))


if __name__ == "__main__":
    unittest.main()
