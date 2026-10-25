"""feature-map: `features.py check` must go red when the code drifts from the map."""
import os, subprocess, tempfile, unittest

from _helpers import run

APP = """import svc
from flask import Flask
app = Flask(__name__)

@app.route("/checkout")
def checkout():
    return str(svc.place_order())
"""
SVC = "def place_order():\n    return 1\n"
UI = """<button data-testid="pay-btn">Pay</button>
<script>hotkeys('ctrl+enter', submit)</script>
"""
VERIFY = "## Checkout\n- test: `python -m pytest -q`\n"
MAP = """## Checkout
- what: Pay for the cart and get an order id.
- route: `/checkout` @ src/app.py
- click: `[data-testid=pay-btn]` @ src/ui.html
- shortcut: `Ctrl+Enter` @ src/ui.html
- trace: `checkout` @ src/app.py > `place_order` @ src/svc.py
- verify: Checkout
- status: {status}
"""


def git(repo, *args):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=repo,
                          capture_output=True, text=True, check=True).stdout.strip()


class CheckDrift(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        os.makedirs(os.path.join(self.repo, "src"))
        for rel, text in (("src/app.py", APP), ("src/svc.py", SVC), ("src/ui.html", UI),
                          ("VERIFY.md", VERIFY)):
            self.write(rel, text)
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        self.sha = git(self.repo, "rev-parse", "--short", "HEAD")
        self.write_map(f"proven @ {self.sha}: drove /checkout, order id shown")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        with open(os.path.join(self.repo, rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def write_map(self, status):
        self.write("FEATURES.md", MAP.format(status=status))

    def edit(self, rel, old, new):
        with open(os.path.join(self.repo, rel), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn(old, text)
        self.write(rel, text.replace(old, new))

    def check(self):
        return run("features.py", "check", self.repo, "--strict")

    def test_accurate_map_passes_strict(self):
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn("0 stale | 0 broken | 0 untraced | 0 unmapped | 0 unlinked | 0 unlabeled | "
                      "0 undescribed | 0 drifted | 0 unpinned", out)

    def test_renamed_selector_is_stale(self):
        self.edit("src/ui.html", 'data-testid="pay-btn"', 'data-testid="pay-btn-v2"')
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("STALE  click  [data-testid=pay-btn]", out)

    def test_changed_shortcut_combo_is_stale(self):
        self.edit("src/ui.html", "'ctrl+enter'", "'ctrl+shift+enter'")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("STALE  shortcut  Ctrl+Enter", out)

    def test_call_left_only_in_a_comment_is_broken(self):
        self.edit("src/app.py", "    return str(svc.place_order())",
                  "    # TODO: call svc.place_order() again\n    return 'ok'")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("BROKEN  trace  place_order is not called from src/app.py", out)

    def test_verify_link_without_verify_md_is_unlinked(self):
        os.remove(os.path.join(self.repo, "VERIFY.md"))
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("no VERIFY.md", out)
        self.assertIn("1 unlinked", out)

    def test_proven_without_commit_pin_is_unpinned(self):
        self.write_map("proven: drove /checkout, order id shown")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("1 unpinned", out)

    def test_route_is_not_found_by_a_substring_of_the_file_path(self):
        self.edit("FEATURES.md", "- route: `/checkout` @ src/app.py",
                  "- route: `/checkout` @ src/app.py\n- route: `/s` @ src/app.py")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("STALE  route  /s @ src/app.py", out)


if __name__ == "__main__":
    unittest.main()
