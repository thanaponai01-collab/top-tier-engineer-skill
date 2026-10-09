#!/usr/bin/env python3
"""
features.py — the feature map behind feature-map (FEATURES.md).

Run them all with `python -m unittest discover tests`.
"""
import os, tempfile, unittest

from _helpers import run


def write(root, rel, text=""):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def app(tmp):
    """A small system with one entry point of each kind: route, click, shortcut, cli."""
    write(tmp, "src/app.py", 'from flask import Flask\napp = Flask(__name__)\n\n'
                             'from svc import place_order\n\n'
                             '@app.route("/checkout")\ndef checkout():\n    return place_order()\n')
    write(tmp, "src/svc.py", 'def place_order():\n    save("orders")\n')
    write(tmp, "src/cart.html", '<button data-testid="pay-btn">Pay</button>\n')
    write(tmp, "src/main.js", "const menu = [{ label: 'Open', accelerator: 'CmdOrCtrl+O' }];\n")
    write(tmp, "cli.py", 'sub.add_parser("export")\n')
    write(tmp, "node_modules/x/lib.js", "app.get('/junk', h)\n")


MAP = """# FEATURES

## Checkout
- what: Pay for the cart and get an order id.
- route: `/checkout` @ src/app.py
- click: `[data-testid=pay-btn]` @ src/cart.html
- trace: `checkout` @ src/app.py > `place_order` @ src/svc.py > `orders` @ src/svc.py
- verify: Checkout
- status: proven: drove /checkout in a browser, order id shown

## Open file
- what: Open a document from disk.
- shortcut: `Ctrl+O` @ src/main.js
- trace: `accelerator` @ src/main.js
- verify: Open
- status: traced: menu template read, accelerator wired

## Export
- what: Write the current document to a file.
- cli: `tool export` @ cli.py
- trace: `add_parser` @ cli.py
- verify: Export
- status: proven: ran `tool export`, file written
"""

VERIFY = "# VERIFY\n\n## Checkout\n- test: `x`\n\n## Open\n- test: `x`\n\n## Export\n- test: `x`\n"


def setup(tmp, features=MAP, verify=VERIFY):
    app(tmp)
    write(tmp, "FEATURES.md", features)
    if verify is not None:
        write(tmp, "VERIFY.md", verify)


class Init(unittest.TestCase):
    def test_drafts_entry_points_of_every_kind_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            app(tmp)
            code, out, err = run("features.py", "init", tmp)
            self.assertEqual(code, 0, err)
            with open(os.path.join(tmp, "FEATURES.md"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("`/checkout`", text)
            self.assertIn("[data-testid=pay-btn]", text)
            self.assertIn("`CmdOrCtrl+O`", text)
            self.assertIn("`export`", text)
            self.assertNotIn("junk", text)
            code, out, _ = run("features.py", "init", tmp)
            self.assertEqual(code, 2)
            self.assertIn("not overwriting", out)

    def test_a_draft_is_not_a_finished_map(self):
        """TODO placeholders must not read as a described, labelled feature."""
        with tempfile.TemporaryDirectory() as tmp:
            app(tmp)
            run("features.py", "init", tmp)
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("undescribed", out)
            self.assertNotIn("STALE", out)


class Check(unittest.TestCase):
    def test_a_true_map_is_clean_even_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            code, out, err = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 0, out + err)
            self.assertIn("0 stale", out)

    def test_a_renamed_selector_goes_stale(self):
        """The fail-proof: change the code under a mapped entry and the check must go red."""
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            write(tmp, "src/cart.html", '<button data-testid="buy-now">Pay</button>\n')
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("STALE", out)
            self.assertIn("pay-btn", out)

    def test_a_missing_file_goes_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            os.remove(os.path.join(tmp, "src", "app.py"))
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("src/app.py", out)

    def test_a_new_entry_point_is_unmapped_and_only_strict_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            write(tmp, "src/admin.py", '@app.route("/admin")\ndef admin(): pass\n')
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("/admin", out)
            self.assertIn("1 unmapped", out)
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 1, out)

    def test_shortcut_modifiers_are_normalised(self):
        """Ctrl+O in the map and CmdOrCtrl+O in the code are the same shortcut."""
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 0, out)
            self.assertNotIn("unmapped", out.replace("0 unmapped", ""))

    def test_verify_link_must_name_a_real_verify_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp, verify="# VERIFY\n\n## Checkout\n- test: `x`\n\n## Reports\n- test: `x`\n")
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("Open", out)
            self.assertIn("Reports", out)

    def test_a_feature_without_a_status_label_is_unlabeled(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp, features=MAP.replace("- status: proven: ran `tool export`, file written\n", ""))
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("1 unlabeled", out)

    def test_a_true_trace_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 0, out)
            self.assertIn("0 broken", out)

    def test_a_renamed_callee_breaks_the_chain(self):
        """The fail-proof: the handler stops calling the service, so the path is no longer real."""
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            write(tmp, "src/app.py", '@app.route("/checkout")\ndef checkout():\n    return order()\n')
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("BROKEN", out)
            self.assertIn("place_order", out)

    def test_a_step_missing_from_its_file_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            write(tmp, "src/svc.py", "def other():\n    pass\n")
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("STALE", out)

    def test_a_same_file_callee_that_is_never_called_is_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "a.py", "def one():\n    pass\n\ndef two():\n    pass\n")
            write(tmp, "FEATURES.md", "## X\n- what: x\n- trace: `one` @ a.py > `two` @ a.py\n"
                  "- status: traced: read a.py\n")
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("BROKEN", out)

    def test_untraced_feature_fails_only_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp, features=MAP.replace("- trace: `add_parser` @ cli.py\n", ""))
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("1 untraced", out)
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 1, out)

    def test_no_map_is_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 2)
            self.assertIn("init", out)

    def test_explicit_needle_overrides_the_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "src/keys.js", "bind('meta+k', openPalette)\n")
            write(tmp, "FEATURES.md", "## Palette\n- what: Open the palette.\n"
                  "- shortcut: `Cmd+K` @ src/keys.js :: openPalette\n- status: traced: read keys.js\n")
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 0, out)


def git(tmp, *args):
    import subprocess
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=tmp,
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()


def repo_at_head(tmp, features=MAP):
    setup(tmp, features)
    git(tmp, "init", "-q")
    git(tmp, "add", "-A")
    git(tmp, "commit", "-qm", "base")
    return git(tmp, "rev-parse", "--short", "HEAD")


class Impact(unittest.TestCase):
    def test_a_changed_file_names_its_feature_and_its_verify_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            code, out, err = run("features.py", "impact", tmp, "--files", "src/svc.py")
            self.assertEqual(code, 0, err)
            self.assertIn("Checkout", out)
            self.assertIn("verify: Checkout", out)
            self.assertNotIn("Export", out)

    def test_a_changed_code_file_no_feature_claims_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            write(tmp, "src/orphan.py", "x = 1\n")
            code, out, _ = run("features.py", "impact", tmp, "--files", "src/orphan.py")
            self.assertEqual(code, 0)
            self.assertIn("claimed by no feature", out)
            self.assertIn("src/orphan.py", out)

    def test_reads_the_change_from_git_when_no_files_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_at_head(tmp)
            write(tmp, "cli.py", 'sub.add_parser("export")\n# edited\n')
            code, out, err = run("features.py", "impact", tmp)
            self.assertEqual(code, 0, err)
            self.assertIn("Export", out)
            self.assertNotIn("Checkout", out)


class Drift(unittest.TestCase):
    def test_drift_is_reported_and_fails_only_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            git(tmp, "init", "-q"); git(tmp, "add", "-A"); git(tmp, "commit", "-qm", "base")
            sha = git(tmp, "rev-parse", "--short", "HEAD")
            mapped = MAP.replace("proven: drove", f"proven @ {sha}: drove")
            write(tmp, "FEATURES.md", mapped)
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 0, out)
            self.assertIn("0 drifted", out)
            write(tmp, "src/svc.py", 'def place_order():\n    save("orders")  # changed\n')
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("drifted", out)
            self.assertIn("1 drifted", out)
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 1, out)

    def test_an_unknown_commit_counts_as_drifted(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp)
            git(tmp, "init", "-q"); git(tmp, "add", "-A"); git(tmp, "commit", "-qm", "base")
            write(tmp, "FEATURES.md", MAP.replace("proven: drove", "proven @ deadbee: drove"))
            code, out, _ = run("features.py", "check", tmp)
            self.assertIn("1 drifted", out)


class JourneySections(unittest.TestCase):
    def test_a_verify_journey_section_is_not_an_orphan_feature(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp, verify=VERIFY + "\n## Journey: Buy it\n- features: Checkout, Export\n- test: `x`\n")
            code, out, _ = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 0, out)
            self.assertNotIn("linked from no feature", out)


class SplitMap(unittest.TestCase):
    """A map past its budget becomes an index of area files; check must read through it."""

    def split(self, tmp):
        head, rest = MAP.split("## Open file", 1)
        write(tmp, "features/checkout.md", head.replace("# FEATURES\n", ""))
        write(tmp, "features/desktop.md", "## Open file" + rest)
        write(tmp, "verify/all.md", VERIFY.replace("# VERIFY\n", ""))

    def test_an_index_of_included_area_files_checks_like_one_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp, features="# FEATURES\n- include: `features/checkout.md` (pay)\n"
                                "- include: features/desktop.md\n",
                  verify="# VERIFY\ninclude: verify/all.md\n")
            self.split(tmp)
            code, out, err = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 0, out + err)
            self.assertIn("3 features", out)

    def test_staleness_inside_an_included_file_is_still_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp, features="include: features/checkout.md\ninclude: features/desktop.md\n")
            self.split(tmp)
            write(tmp, "src/cart.html", "<button>Pay</button>\n")
            code, out, _ = run("features.py", "check", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("pay-btn", out)

    def test_an_include_cycle_does_not_hang(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup(tmp, features="include: features/a.md\n")
            write(tmp, "features/a.md", "include: FEATURES.md\n" + MAP.replace("# FEATURES\n", ""))
            code, out, err = run("features.py", "check", tmp, "--strict")
            self.assertEqual(code, 0, out + err)


if __name__ == "__main__":
    unittest.main()


