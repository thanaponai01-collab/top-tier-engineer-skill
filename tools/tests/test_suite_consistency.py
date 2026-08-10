#!/usr/bin/env python3
"""Suite-wide self-description checks that don't belong to any single tool."""
import os, unittest
from _helpers import HERE


class SuiteConsistency(unittest.TestCase):
    """The suite's self-description must match the filesystem. A current-state doc
    that names the skill count as a word (PROTOCOL, the plugin manifest) must use the
    word matching the number of skills/ dirs. Earned: 'eighteen skills' shipped into
    PROTOCOL §title while the suite had nineteen — the drift-arbiter file drifted."""

    WORDS = {16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
             20: "twenty", 21: "twenty-one", 22: "twenty-two"}

    # Every pure current-state surface that states the count. README is excluded on
    # purpose: it mixes current and historical counts ("seventeenth skill" narrates a
    # past milestone), so a strict no-neighbour check would false-fail on real history.
    SURFACES = ("PROTOCOL.md", "MAP.md",
                os.path.join(".claude-plugin", "plugin.json"),
                os.path.join(".claude-plugin", "marketplace.json"))

    def test_skill_count_matches_current_state_claims(self):
        root = os.path.dirname(HERE)
        n = sum(1 for e in os.scandir(os.path.join(root, "skills")) if e.is_dir())
        self.assertIn(n, self.WORDS, f"extend WORDS past {n} skills")
        right = self.WORDS[n]
        for rel in self.SURFACES:
            text = open(os.path.join(root, rel), encoding="utf-8").read().lower()
            self.assertIn(right, text, f"{rel} never states the {right}-skill count")
            # Phrasing-independent: a neighbour count word anywhere in a current-state
            # surface is drift, whether it reads "eighteen skills" or "eighteen wired
            # engineering skills". (The bug that shipped was the former; the manifests
            # use the latter, which an adjacency-only check would miss.)
            for k in (n - 1, n + 1):
                self.assertNotIn(self.WORDS[k], text,
                                 f"{rel} names {self.WORDS[k]}; filesystem has {n} skills")


if __name__ == "__main__":
    unittest.main()
