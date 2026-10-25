"""feature-map: `features.py check` must go red when the code drifts from the map."""
import os, shutil, subprocess, sys, tempfile, unittest

from _helpers import run, SCRIPTS

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
FLAG = "python -c \"import os,sys; os.path.exists('src/ok.flag') or (print('expected order id'), sys.exit(1))\""
VERIFY = (f"## Checkout\n- path: src/\n- test: `{FLAG}`\n- fail-signal: expected order id\n"
          "- fail-proof: removed src/ok.flag, check went red\n")
ANNOUNCED = "Read FEATURES.md first; `python .features/features.py check --rerun` says what broke.\n"
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
                          ("VERIFY.md", VERIFY), ("AGENTS.md", ANNOUNCED)):
            self.write(rel, text)
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        self.sha = git(self.repo, "rev-parse", "--short", "HEAD")
        self.prove()
        self.write_map("proven: drove /checkout, order id shown")
        self.receipt()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        with open(os.path.join(self.repo, rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def prove(self):
        """verify-loop sees the check go red on the wrong product, then pass on the right one."""
        flag = os.path.join(self.repo, "src", "ok.flag")
        if os.path.exists(flag):
            os.remove(flag)
        run("verify.py", "run", self.repo)
        self.write("src/ok.flag", "")
        run("verify.py", "run", self.repo)

    def receipt(self):
        """features.py prove: run the route, record the click and shortcut from a screenshot."""
        self.write("shot.txt", "order id 42 shown after pay-btn and ctrl+enter")
        code, out, _ = run("features.py", "prove", "--repo", self.repo, "--feature", "Checkout", "--",
                           sys.executable, "-c", "print('order id 42')", "/checkout")
        self.assertEqual(code, 0, out)
        code, out, _ = run("features.py", "prove", "--repo", self.repo, "--feature", "Checkout",
                           "--entry", "click: [data-testid=pay-btn]", "--entry", "shortcut: Ctrl+Enter",
                           "--file", "shot.txt", "--note", "order id shown")
        self.assertEqual(code, 0, out)

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
                      "0 undescribed | 0 drifted | 0 unproven | 0 unbacked | 0 unfenced", out)

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

    def test_proven_without_receipt_is_unproven(self):
        shutil.rmtree(os.path.join(self.repo, ".features"))
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("unproven: proven, but no receipt in .features/checkout.json", out)
        self.assertIn("1 unproven", out)
        # check says how to prove each entry, so the agent never reads this script to find out
        self.assertIn('--feature "Checkout" --entry "route: /checkout" -- <the command that drives it>', out)
        self.assertIn('--entry "click: [data-testid=pay-btn]" --file <screenshot in the repo>', out)

    def test_map_alone_passes_strict_without_verify_loop(self):
        os.remove(os.path.join(self.repo, "VERIFY.md"))
        self.edit("FEATURES.md", "- verify: Checkout\n", "")
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn("0 unlinked", out)

    def test_missing_verify_line_counts_once_the_repo_uses_verify_loop(self):
        self.edit("FEATURES.md", "- verify: Checkout\n", "")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("no verify link to a VERIFY.md section", out)

    def test_traced_needs_no_receipt(self):
        shutil.rmtree(os.path.join(self.repo, ".features"))
        self.write_map("traced: read checkout to place_order")
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)

    def test_route_is_not_found_by_a_substring_of_the_file_path(self):
        self.edit("FEATURES.md", "- route: `/checkout` @ src/app.py",
                  "- route: `/checkout` @ src/app.py\n- route: `/s` @ src/app.py")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("STALE  route  /s @ src/app.py", out)


    def test_proven_without_verify_receipt_is_unbacked(self):
        for name in os.listdir(self.repo):
            if name.startswith(".verify-state"):
                os.remove(os.path.join(self.repo, name))
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("unbacked: no verify-loop receipt shows 'Checkout' rejecting", out)
        self.assertIn("1 unbacked", out)

    def test_proven_with_failing_verify_check_is_unbacked(self):
        os.remove(os.path.join(self.repo, "src", "ok.flag"))
        run("verify.py", "run", self.repo)
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("unbacked: a check of 'Checkout' failed in the last verify-loop run", out)

    def test_feature_file_outside_verify_path_is_unfenced(self):
        self.edit("VERIFY.md", "- path: src/\n", "- path: src/app.py\n")
        self.prove()
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("unfenced: src/svc.py, src/ui.html outside the path: of 'Checkout'", out)
        self.assertIn("1 unfenced", out)

    def test_verify_section_without_path_is_unfenced(self):
        self.edit("VERIFY.md", "- path: src/\n", "")
        self.prove()
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("unfenced: 'Checkout' in VERIFY.md has no path:", out)

    def test_without_verify_loop_receipts_are_not_judged(self):
        for name in os.listdir(self.repo):
            if name.startswith(".verify-state"):
                os.remove(os.path.join(self.repo, name))
        with tempfile.TemporaryDirectory() as skills:
            alone = os.path.join(skills, "feature-map", "scripts")
            shutil.copytree(SCRIPTS["features.py"], alone, ignore=shutil.ignore_patterns("__pycache__"))
            p = subprocess.run([sys.executable, os.path.join(alone, "features.py"), "check", self.repo,
                                "--strict"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("receipts not checked: verify-loop is not installed beside feature-map", p.stdout)

    # ---- prove: receipts behind `proven` ------------------------------------------------------

    def prove_cmd(self, *cmd, entry=()):
        args = ["prove", "--repo", self.repo, "--feature", "Checkout"]
        for e in entry:
            args += ["--entry", e]
        return run("features.py", *args, "--", *cmd)

    def test_code_change_after_proof_is_drifted_until_re_proven(self):
        self.edit("src/svc.py", "return 1", "return 2")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("drifted: src/svc.py changed since", out)
        self.receipt()
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)

    def test_line_endings_alone_are_not_drift(self):
        with open(os.path.join(self.repo, "src", "svc.py"), "w", encoding="utf-8", newline="\r\n") as fh:
            fh.write(SVC)
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)

    def test_failing_run_is_recorded_but_is_not_proof(self):
        code, out, _ = self.prove_cmd(sys.executable, "-c", "import sys; sys.exit('boom')", "/checkout")
        self.assertEqual(code, 1, out)
        self.assertIn("FAILED (exit 1)", out)
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("unproven: route: /checkout: its run exited 1", out)

    def test_receipt_keeps_no_local_repo_path(self):
        self.prove_cmd(sys.executable, "-c", "import os; print(os.getcwd())", "/checkout")
        with open(os.path.join(self.repo, ".features", "checkout.json"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("<repo>", text)
        self.assertNotIn(os.path.basename(self.repo), text)

    def test_entry_with_no_receipt_is_unproven(self):
        self.edit("FEATURES.md", "- route: `/checkout` @ src/app.py",
                  "- route: `/checkout` @ src/app.py\n- route: `/pay` @ src/app.py")
        self.edit("src/app.py", '@app.route("/checkout")', '@app.route("/checkout")\n@app.route("/pay")')
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("unproven: route: /pay has no receipt", out)

    def test_swapped_screenshot_is_unproven(self):
        self.write("shot.txt", "something else")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("shot.txt is missing or not the file that was recorded", out)

    def test_command_naming_no_entry_point_is_refused(self):
        code, out, _ = self.prove_cmd(sys.executable, "-c", "print('hi')")
        self.assertEqual(code, 2, out)
        self.assertIn("names none of the entry points", out)

    def test_unknown_entry_is_refused(self):
        code, out, _ = self.prove_cmd(sys.executable, "-c", "print(1)", entry=["route: /nope"])
        self.assertEqual(code, 2, out)
        self.assertIn("not an entry point of 'Checkout'", out)

    def test_screenshot_needs_a_note(self):
        code, out, _ = run("features.py", "prove", "--repo", self.repo, "--feature", "Checkout",
                           "--entry", "click: [data-testid=pay-btn]", "--file", "shot.txt")
        self.assertEqual(code, 2, out)

    # ---- the map carries its own alarm -------------------------------------------------------

    def prove_real(self):
        """A receipt whose command really depends on the code: place_order must return 1."""
        code, out = self.prove_cmd(sys.executable, "-c",
                                   "import sys; sys.path.insert(0, 'src'); import svc; "
                                   "sys.exit(0 if svc.place_order() == 1 else 'no order id')", "/checkout")[:2]
        self.assertEqual(code, 0, out)

    def test_rerun_fails_when_a_proven_run_breaks(self):
        self.prove_real()
        self.edit("src/svc.py", "return 1", "return None")
        code, out, _ = run("features.py", "check", self.repo, "--rerun")
        self.assertEqual(code, 1, out)
        self.assertIn("FAILS  route: /checkout:", out)
        self.assertIn("no order id", out)
        self.assertIn("1 regressed", out)

    def test_rerun_passes_when_runs_still_pass(self):
        self.prove_real()
        code, out, _ = run("features.py", "check", self.repo, "--strict", "--rerun")
        self.assertEqual(code, 0, out)
        self.assertIn("rerun  route: /checkout: exit 0, as recorded", out)
        self.assertIn("0 regressed", out)

    def test_prove_again_re_pins_passing_runs_and_records_failing_ones(self):
        self.prove_real()
        self.edit("src/app.py", "def checkout():", "def checkout():  # moved")
        code, out, _ = self.check()
        self.assertIn("drifted", out)
        code, out, _ = run("features.py", "prove", "--repo", self.repo, "--again")
        self.assertEqual(code, 0, out)
        # a screenshot cannot be re-taken by a script: it is named for redoing, and stays drifted
        self.assertIn("was shown in shot.txt; drive it again", out)
        code, out, _ = self.check()
        self.assertIn("since click: [data-testid=pay-btn]; shortcut: Ctrl+Enter was proven", out)
        self.assertNotIn("since route: /checkout was proven", out)
        self.edit("src/svc.py", "return 1", "return None")
        code, out, _ = run("features.py", "prove", "--repo", self.repo, "--again")
        self.assertEqual(code, 1, out)
        self.assertIn("FAILED", out)
        code, out, _ = self.check()
        self.assertIn("unproven: route: /checkout: its run exited 1", out)

    def test_check_says_what_ran_where(self):
        code, out, _ = self.check()
        self.assertIn("Proof: ran here: /checkout; shown in a file: [data-testid=pay-btn], Ctrl+Enter", out)
        run("features.py", "prove", "--repo", self.repo, "--feature", "Checkout", "--copy",
            "--", sys.executable, "-c", "print(1)", "/checkout")
        code, out, _ = self.check()
        self.assertIn("Proof: ran in a throwaway copy: /checkout;", out)

    def test_renamed_entry_point_takes_its_old_receipt_with_it(self):
        self.edit("src/app.py", '@app.route("/checkout")', '@app.route("/pay")')
        self.edit("FEATURES.md", "- route: `/checkout` @ src/app.py", "- route: `/pay` @ src/app.py")
        code, out, _ = run("features.py", "check", self.repo, "--rerun")
        self.assertNotIn("route: /checkout", out)  # the old receipt is neither checked nor re-run
        self.assertIn("unproven: route: /pay has no receipt", out)
        self.prove_cmd(sys.executable, "-c", "print('order id')", "/pay")
        with open(os.path.join(self.repo, ".features", "checkout.json"), encoding="utf-8") as fh:
            self.assertNotIn("route: /checkout", fh.read())

    def test_copy_keeps_writes_out_of_the_repo(self):
        write = "open('wrote.txt', 'w').write('x')"
        self.prove_cmd(sys.executable, "-c", write, "/checkout")
        self.assertTrue(os.path.exists(os.path.join(self.repo, "wrote.txt")))
        os.remove(os.path.join(self.repo, "wrote.txt"))
        code, out, _ = run("features.py", "prove", "--repo", self.repo, "--feature", "Checkout", "--copy",
                           "--", sys.executable, "-c", write, "/checkout")
        self.assertEqual(code, 0, out)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "wrote.txt")))

    def test_vendored_checker_runs_without_the_skill_and_is_not_scanned(self):
        vendored = os.path.join(self.repo, ".features", "features.py")
        self.assertTrue(os.path.isfile(vendored))
        p = subprocess.run([sys.executable, vendored, "check", self.repo, "--rerun"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("0 unmapped", p.stdout)

    def test_map_no_agent_file_points_at_is_unannounced(self):
        os.remove(os.path.join(self.repo, "AGENTS.md"))
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("1 unannounced", out)
        self.assertIn("Read FEATURES.md before driving or changing this app.", out)
        self.write("CLAUDE.md", "Read FEATURES.md.\n")  # names the map but not its check
        code, out, _ = self.check()
        self.assertIn("1 unannounced", out)
        self.write("CLAUDE.md", "Read FEATURES.md; run `python .features/features.py check --rerun`.\n")
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)

    def test_failing_label_needs_a_failed_run(self):
        self.write_map("failing: checkout crashes")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("failing, but no failed run is recorded", out)
        self.prove_cmd(sys.executable, "-c", "import sys; sys.exit('500')", "/checkout")
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)

    # ---- trace starts where the user does ----------------------------------------------------

    def test_first_trace_step_unreachable_from_entry_is_broken(self):
        self.write("src/other.py", "import svc\ndef helper():\n    return svc.place_order()\n")
        self.edit("FEATURES.md", "- trace: `checkout` @ src/app.py > `place_order` @ src/svc.py",
                  "- trace: `helper` @ src/other.py > `place_order` @ src/svc.py")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("BROKEN  trace  helper, the first step, is not reached from the entry point file", out)

    def test_first_trace_step_called_from_entry_file_is_fine(self):
        self.edit("FEATURES.md", "- trace: `checkout` @ src/app.py > `place_order` @ src/svc.py",
                  "- trace: `place_order` @ src/svc.py")
        self.receipt()
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)

    # ---- Not features ----------------------------------------------------------------------

    def add_debug_button(self):
        self.edit("src/ui.html", "<script>", '<button id="debug-dump">dump</button>\n<script>')
        self.receipt()

    def test_unlisted_debug_control_is_unmapped(self):
        self.add_debug_button()
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("1 unmapped", out)

    def test_not_feature_with_reason_is_not_unmapped(self):
        self.add_debug_button()
        with open(os.path.join(self.repo, "FEATURES.md"), "a", encoding="utf-8") as fh:
            fh.write("\n## Not features\n- click: `#debug-dump` @ src/ui.html: developer dump, hidden in prod\n"
                     "\n## Not built\nRefunds are planned.\n")
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn("1 features |", out)
        self.assertIn("0 unmapped", out)
        self.assertIn("1 not features", out)

    def test_not_feature_without_reason_still_counts(self):
        self.add_debug_button()
        with open(os.path.join(self.repo, "FEATURES.md"), "a", encoding="utf-8") as fh:
            fh.write("\n## Not features\n- click: `#debug-dump` @ src/ui.html\n")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("no reason given", out)
        self.assertIn("1 unmapped", out)

    def test_not_feature_gone_from_code_is_stale(self):
        with open(os.path.join(self.repo, "FEATURES.md"), "a", encoding="utf-8") as fh:
            fh.write("\n## Not features\n- click: `#debug-dump` @ src/ui.html: developer dump\n")
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("STALE  click  #debug-dump", out)


class CliAnchor(unittest.TestCase):
    CLI = ('import argparse\nfrom commands import search\nHANDLERS = {"search": search.run}\n'
           'p = argparse.ArgumentParser()\ns = p.add_subparsers()\ns.add_parser("search")\n')

    def check_map(self, cli):
        with tempfile.TemporaryDirectory() as repo:
            with open(os.path.join(repo, "cli.py"), "w", encoding="utf-8") as fh:
                fh.write(cli)
            with open(os.path.join(repo, "FEATURES.md"), "w", encoding="utf-8") as fh:
                fh.write("## Search\n- what: find notes\n- cli: `search` @ cli.py\n- status: traced: read it\n")
            return run("features.py", "check", repo)

    def test_declared_subcommand_is_ok(self):
        code, out, _ = self.check_map(self.CLI)
        self.assertEqual(code, 0, out)

    def test_renamed_subcommand_is_stale_though_its_module_keeps_the_name(self):
        code, out, _ = self.check_map(self.CLI.replace('"search"', '"find"'))
        self.assertEqual(code, 1, out)
        self.assertIn("STALE  cli  search", out)

    def test_decorator_named_and_argument_spelled_commands_are_ok(self):
        for cli in ("@cli.command()\ndef search(q):\n    pass\n", "program.command('search <q>')\n"):
            code, out, _ = self.check_map(cli)
            self.assertEqual(code, 0, cli + out)


class Init(unittest.TestCase):
    def test_init_drafts_map_with_its_alarm_and_vendors_the_checker(self):
        with tempfile.TemporaryDirectory() as repo:
            with open(os.path.join(repo, "cli.py"), "w", encoding="utf-8") as fh:
                fh.write("import argparse\np = argparse.ArgumentParser()\ns = p.add_subparsers()\n"
                         "s.add_parser('export')\n")
            code, out, _ = run("features.py", "init", repo)
            self.assertEqual(code, 0, out)
            with open(os.path.join(repo, "FEATURES.md"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("python .features/features.py check --rerun", text)
            self.assertIn("- cli: `export` @ cli.py", text)
            self.assertTrue(os.path.isfile(os.path.join(repo, ".features", "features.py")))
            # one self-contained file, so reading receipts never reads a helper's module
            self.assertEqual(sorted(os.listdir(os.path.join(repo, ".features"))), ["features.py"])


if __name__ == "__main__":
    unittest.main()
