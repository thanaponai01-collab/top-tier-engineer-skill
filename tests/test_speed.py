"""1.10.0: the inner loop is fast and shared. A non-strict run re-hashes only files whose stat data
changed; a check result already proved for the same command and content is reused across agents and
worktrees; parallel checks each get their own slot and port.

Run with: python -m unittest discover tests
"""
import json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path

from _helpers import run

PASS = 'python -c "pass"'


def write(root, rel, text="", age=10):
    """Write a file whose mtime is `age` seconds old, so the stat cache may trust it."""
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    t = time.time() - age
    os.utime(p, (t, t))


def run_json(*args):
    code, out, err = run("verify.py", "run", *args, "--json")
    return code, json.loads(out)


class FastTreeSignature(unittest.TestCase):
    def repo(self, root):
        write(root, "VERIFY.md", f"## A\n- test: `{PASS}`\n- fail-proof: x\n")
        for i in range(5):
            write(root, f"src/m{i}.py", f"x = {i}\n")

    def test_non_strict_run_rehashes_only_changed_files_and_strict_reads_all(self):
        with tempfile.TemporaryDirectory() as root:
            self.repo(root)
            _, first = run_json(root)
            self.assertEqual(first["tree_sig"]["mode"], "fast")
            _, warm = run_json(root)
            self.assertEqual((warm["tree_sig"]["hashed"], warm["tree_sig"]["files"]), (0, 6))
            write(root, "src/m1.py", "x = 'edited'\n", age=20)
            _, edited = run_json(root)
            self.assertEqual(edited["tree_sig"]["hashed"], 1)
            _, strict = run_json(root, "--strict")
            self.assertEqual((strict["tree_sig"]["mode"], strict["tree_sig"]["hashed"]), ("full", 6))

    def test_fast_and_full_signatures_agree_so_status_reads_partial_not_stale(self):
        with tempfile.TemporaryDirectory() as root:
            self.repo(root)
            run_json(root)
            run_json(root)  # recorded from the warm stat cache
            code, out, _ = run("verify.py", "status", root, "--json")
            self.assertEqual(json.loads(out)["state"], "partial", out)

    def test_status_still_reads_every_byte_and_catches_an_edit_that_restores_timestamps(self):
        with tempfile.TemporaryDirectory() as root:
            self.repo(root)
            run_json(root)
            run_json(root)
            p = Path(root, "src/m2.py")
            st = os.stat(p)
            p.write_text("x = 9\n", encoding="utf-8")  # same size as "x = 2\n"
            os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
            code, out, _ = run("verify.py", "status", root, "--json")
            self.assertEqual(json.loads(out)["state"], "stale", out)

    def test_a_file_written_this_instant_is_never_trusted_from_the_cache(self):
        with tempfile.TemporaryDirectory() as root:
            self.repo(root)
            write(root, "src/new.py", "y = 1\n", age=0)
            run_json(root)
            _, again = run_json(root)
            self.assertEqual(again["tree_sig"]["hashed"], 1)  # too fresh to cache: hashed again

    def test_cache_lives_outside_the_signature_and_scratch_copies(self):
        with tempfile.TemporaryDirectory() as root:
            self.repo(root)
            _, a = run_json(root)
            _, b = run_json(root)
            self.assertEqual(b["tree_sig"]["files"], 6)  # the cache itself is not a tree file
            self.assertTrue(any(n.startswith(".verify-state") for n in os.listdir(root)))


COUNT = "python count.py"  # appends a line to $RUNS_LOG each time it really runs
COUNTER = "import os\nopen(os.environ['RUNS_LOG'], 'a').write('ran\\n')\n"


def git(root, *args):
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True)


class SharedResultCache(unittest.TestCase):
    def repo(self, root):
        write(root, "VERIFY.md", f"## A\n- test: `{COUNT}`\n- fail-proof: x\n")
        write(root, "count.py", COUNTER)
        write(root, "app.py", "x = 1\n")

    def runs(self):
        return len(Path(self.log).read_text().splitlines()) if Path(self.log).exists() else 0

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "repo")
        self.log = os.path.join(self.tmp.name, "runs.log")
        os.environ["RUNS_LOG"] = self.log

    def tearDown(self):
        os.environ.pop("RUNS_LOG", None)
        self.tmp.cleanup()

    def test_same_command_on_same_content_is_reused_and_reported(self):
        self.repo(self.root)
        code, first = run_json(self.root)
        self.assertEqual((code, self.runs(), first["summary"]["cached"]), (0, 1, 0))
        code, second = run_json(self.root)
        self.assertEqual((code, self.runs()), (0, 1), "a proved pass on unchanged content ran again")
        self.assertEqual(second["summary"]["cached"], 1)
        self.assertTrue(second["results"][0]["cached"])
        code, out, _ = run("verify.py", "run", self.root)
        self.assertIn("CACHED", out)
        write(self.root, "app.py", "x = 2\n", age=30)
        run_json(self.root)
        self.assertEqual(self.runs(), 2, "an edit must invalidate the cached pass")

    def test_no_cache_always_runs(self):
        self.repo(self.root)
        run_json(self.root)
        code, again = run_json(self.root, "--no-cache")
        self.assertEqual((self.runs(), again["summary"]["cached"]), (2, 0))

    def test_a_failure_is_never_cached(self):
        self.repo(self.root)
        write(self.root, "count.py", COUNTER + "print('expected 1')\nraise SystemExit(1)\n")
        run_json(self.root)
        code, again = run_json(self.root)
        self.assertEqual((code, self.runs()), (1, 2))

    def test_worktrees_share_the_cache_through_the_common_git_dir(self):
        main, other = os.path.join(self.tmp.name, "main"), os.path.join(self.tmp.name, "other")
        os.makedirs(main)
        git(main, "init", "-q")
        self.repo(main)
        git(main, "add", "-A")
        git(main, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x")
        git(main, "worktree", "add", "-q", other)
        for p in Path(other).rglob("*"):
            if ".git" not in p.parts and p.is_file():
                t = time.time() - 10
                os.utime(p, (t, t))
        run_json(main)
        code, there = run_json(other)
        self.assertEqual((code, self.runs(), there["summary"]["cached"]), (0, 1, 1))
        self.assertTrue(Path(main, ".git", "verify-loop", "results.json").exists())

    def test_a_fast_recorded_pass_never_satisfies_strict(self):
        self.repo(self.root)
        run_json(self.root)  # non-strict: keyed by the fast signature
        _, strict = run_json(self.root, "--strict")
        self.assertEqual((self.runs(), strict["summary"]["cached"]), (2, 0))
        _, strict2 = run_json(self.root, "--strict")  # a strict pass is keyed by the full signature
        self.assertEqual((self.runs(), strict2["summary"]["cached"]), (2, 1))

    def test_fixture_edits_change_the_signature(self):
        self.repo(self.root)
        write(self.root, "tests/fixtures/data.json", "{}")
        run_json(self.root)
        write(self.root, "tests/fixtures/data.json", "[]", age=30)
        run_json(self.root)
        self.assertEqual(self.runs(), 2, "a fixture is an input: editing it must re-run the check")


SERVE = ("import os, socket, sys, time\n"
         "slot, port = os.environ['VERIFY_SLOT'], int(os.environ['VERIFY_PORT'])\n"
         "s = socket.socket()\n"
         "s.bind(('127.0.0.1', port))  # a second check on the same port fails here\n"
         "s.listen()\n"
         "open(os.path.join(os.environ['SLOT_DIR'], sys.argv[1]), 'w').write(f'{slot} {port}')\n"
         "time.sleep(1.0)\n")


class SlotsAndPorts(unittest.TestCase):
    def test_parallel_checks_get_distinct_slots_and_free_ports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, slots = os.path.join(tmp, "repo"), os.path.join(tmp, "slots")
            os.makedirs(slots)
            os.environ["SLOT_DIR"] = slots
            try:
                write(root, "serve.py", SERVE)
                write(root, "VERIFY.md", "".join(f"## F{i}\n- test: `python serve.py f{i}`\n- fail-proof: x\n"
                                                 for i in range(3)))
                code, report = run_json(root, "--jobs", "3")
                self.assertEqual(code, 0, report)
                got = [Path(slots, f"f{i}").read_text().split() for i in range(3)]
                self.assertEqual(sorted(s for s, _ in got), ["0", "1", "2"])
                self.assertEqual(len({p for _, p in got}), 3)
                code, report = run_json(root, "--no-cache")  # serial: everything runs in slot 0
                self.assertEqual(code, 0, report)
                self.assertEqual({Path(slots, f"f{i}").read_text().split()[0] for i in range(3)}, {"0"})
            finally:
                os.environ.pop("SLOT_DIR", None)


if __name__ == "__main__":
    unittest.main()
