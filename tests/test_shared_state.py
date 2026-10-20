"""Many agents, one repo: state writes are atomic and locked, concurrent saves merge instead of
losing each other's evidence, and VERIFY_AGENT gives each agent its own loop memory while the
baseline and rejection receipts stay repo-wide.

Run with: python -m unittest discover tests
"""
import os, subprocess, sys, tempfile, textwrap, time, unittest
from pathlib import Path

from _helpers import SCRIPTS

VERIFY = os.path.join(SCRIPTS["verify.py"], "verify.py")


def write(root, rel, text=""):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def verify(*args, agent=None):
    env = dict(os.environ)
    env.pop("VERIFY_AGENT", None)
    if agent is not None:
        env["VERIFY_AGENT"] = agent
    p = subprocess.run([sys.executable, VERIFY, *args], capture_output=True, text=True,
                       encoding="utf-8", env=env)
    return p.returncode, p.stdout + p.stderr


WORKER = textwrap.dedent("""
    import sys
    sys.path.insert(0, sys.argv[1])
    import verify as v
    repo, name, n = sys.argv[2], sys.argv[3], int(sys.argv[4])
    for i in range(n):
        s = v.load_state(repo)
        s.setdefault("failures", {})[f"{name}|{i}"] = {"signature": "x", "exit": 1, "output": "no"}
        v.save_state(repo, s)
""")

READER = textwrap.dedent("""
    import json, os, sys, time
    path, seconds = sys.argv[1], float(sys.argv[2])
    bad = 0
    end = time.time() + seconds
    while time.time() < end:
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        try:
            json.loads(text)
        except ValueError:
            bad += 1
    print(bad)
""")


class ConcurrentSaves(unittest.TestCase):
    def test_parallel_writers_keep_every_receipt_and_readers_never_see_half_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            worker, reader = Path(tmp, "worker.py"), Path(tmp, "reader.py")
            worker.write_text(WORKER, encoding="utf-8")
            reader.write_text(READER, encoding="utf-8")
            repo = Path(tmp, "repo")
            repo.mkdir()
            subprocess.run([sys.executable, str(worker), SCRIPTS["verify.py"], str(repo), "seed", "1"],
                           check=True)
            watcher = subprocess.Popen([sys.executable, str(reader), str(repo / ".verify-state.json"), "6"],
                                       stdout=subprocess.PIPE, text=True)
            procs = [subprocess.Popen([sys.executable, str(worker), SCRIPTS["verify.py"], str(repo),
                                       f"w{k}", "25"]) for k in range(6)]
            for p in procs:
                self.assertEqual(p.wait(timeout=120), 0)
            torn = int(watcher.communicate(timeout=60)[0].strip())
            self.assertEqual(torn, 0, "a reader saw a partially written state file")
            sys.path.insert(0, SCRIPTS["verify.py"])
            import verify as v
            state = v.load_state(str(repo))
            self.assertFalse(state.get("forged"), "concurrent saves must keep the seal valid")
            self.assertEqual(len(state["failures"]), 6 * 25 + 1, "a concurrent save lost receipts")
            leftovers = sorted(f.name for f in repo.iterdir() if f.name != ".verify-state.json")
            self.assertEqual(leftovers, [], "temp or lock files left behind")

    def test_a_key_this_process_did_not_touch_is_not_reverted(self):
        with tempfile.TemporaryDirectory() as tmp:
            sys.path.insert(0, SCRIPTS["verify.py"])
            import verify as v
            repo = Path(tmp, "repo")
            repo.mkdir()
            v.save_state(str(repo), {"baseline": {"a": "1"}, "rounds": 0})
            # another agent loads now and saves after our baseline lands
            Path(tmp, "stale.py").write_text(textwrap.dedent("""
                import os, sys, time
                sys.path.insert(0, sys.argv[1])
                import verify as v
                repo, go = sys.argv[2], sys.argv[3]
                s = v.load_state(repo)
                open(go + ".loaded", "w").close()
                while not os.path.exists(go):
                    time.sleep(0.01)
                s["rounds"] = 3
                v.save_state(repo, s)
            """), encoding="utf-8")
            go = Path(tmp, "go")
            stale = subprocess.Popen([sys.executable, str(Path(tmp, "stale.py")), SCRIPTS["verify.py"],
                                      str(repo), str(go)])
            while not Path(str(go) + ".loaded").exists() and stale.poll() is None:
                time.sleep(0.01)
            fresh = v.load_state(str(repo))
            fresh["baseline"] = {"a": "2"}
            v.save_state(str(repo), fresh)
            go.write_text("")
            self.assertEqual(stale.wait(timeout=60), 0)
            state = v.load_state(str(repo))
            self.assertEqual(state["baseline"], {"a": "2"}, "a stale save reverted a newer baseline")
            self.assertEqual(state["rounds"], 3)

    def test_a_key_this_process_removed_stays_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            sys.path.insert(0, SCRIPTS["verify.py"])
            import verify as v
            v.save_state(tmp, {"scope": {"allow": ["x"]}, "rounds": 0})
            s = v.load_state(tmp)
            s.pop("scope")
            v.save_state(tmp, s)
            self.assertNotIn("scope", v.load_state(tmp))


RECIPE = ("## Answer\n- test: `python check.py`\n- oracle: check.py\n"
          "- fail-signal: expected 42\n- fail-proof: returned 41, check failed, restored\n")
CHECK = ("from app import answer\nimport sys\n"
         "if answer() != 42:\n    print('expected 42, got', answer()); sys.exit(1)\n")


class PerAgentState(unittest.TestCase):
    def fixture(self, root, value=42):
        write(root, "VERIFY.md", RECIPE)
        write(root, "check.py", CHECK)
        write(root, "app.py", f"def answer(): return {value}\n")

    def test_each_agent_keeps_its_own_loop_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            write(tmp, "app.py", "def answer(): return 41  # wrong on purpose\n")
            self.assertEqual(verify("run", tmp, agent="alpha")[0], 1)
            write(tmp, "app.py", "def answer(): return 42\n")
            verify("baseline", tmp, agent="alpha")
            code, out = verify("run", tmp, "--strict", agent="beta")
            self.assertEqual(code, 0, out)
            self.assertNotIn("NEWLY GREEN", out, "beta must not inherit alpha's loop memory")
            self.assertIn("VERIFY-STATE: green", verify("status", tmp, agent="beta")[1])
            self.assertNotIn("VERIFY-STATE: green", verify("status", tmp, agent="alpha")[1],
                             "alpha's last run was red; beta's green run is not alpha's")
            self.assertTrue(Path(tmp, ".verify-state.beta.json").is_file())
            # alpha running later writes only its own file: beta stays current, not stale
            verify("run", tmp, agent="alpha")
            self.assertIn("VERIFY-STATE: green", verify("status", tmp, agent="beta")[1])

    def test_baseline_and_receipts_are_shared_so_a_new_name_cannot_escape_a_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            write(tmp, "app.py", "def answer(): return 41  # wrong on purpose\n")
            verify("run", tmp, agent="alpha")
            write(tmp, "app.py", "def answer(): return 42\n")
            verify("baseline", tmp, agent="alpha")
            code, out = verify("run", tmp, "--strict", agent="gamma")
            self.assertEqual(code, 0, "alpha's rejection receipt counts for every agent:\n" + out)
            write(tmp, "check.py", "pass\n")
            code, out = verify("run", tmp, agent="gamma")
            self.assertEqual(code, 1, out)
            self.assertIn("CHECK CHANGED", out)
            code, out = verify("baseline", tmp, agent="delta")
            self.assertEqual(code, 1, out)
            self.assertIn("BASELINE REFUSED", out)

    def test_bad_agent_name_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            code, out = verify("run", tmp, agent="../escape")
            self.assertEqual(code, 2, out)
            self.assertIn("VERIFY_AGENT", out)
            self.assertFalse(any(p.name.startswith(".verify-state") for p in Path(tmp).iterdir()))


if __name__ == "__main__":
    unittest.main()
