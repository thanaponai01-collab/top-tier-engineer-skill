"""Posts a refund to a real ledger in dry-run mode: the only check that the ledger accepts the entry."""
import unittest

import poster


class LedgerAcceptsRefund(unittest.TestCase):
    def test_ledger_accepts_the_refund_entry(self):
        out = poster.post_refund("A-1", 12.50)
        self.assertIn("accepted", out)


if __name__ == "__main__":
    unittest.main()
