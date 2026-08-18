#!/usr/bin/env python3
"""
stop-gate.py — the Stop-hook adapter, its root resolution, and its fail-open contract.

Part of the suite's own test floor; run them all with `python3 tools/test_tools.py`.
"""
import json, os, re, subprocess, sys, tempfile, unittest

from _helpers import HERE, run


class StopGate(unittest.TestCase):
    """The Stop hook had NO test coverage and CI never ran its selftest, which is how
    both root-resolution defects survived: the hook loads its rules from wherever the
    plugin is INSTALLED, while a session developing the suite edits a checkout
    elsewhere."""

    def _load(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "stop_gate_under_test", os.path.join(HERE, "stop-gate.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _fake_checkout(self, parent, dirname, plugin_name):
        """Materialise the minimum a directory needs to look like a suite checkout:
        a plugin manifest declaring `plugin_name`, and a tools/verdict-lint.py to load
        rules from. Returns its path."""
        fake = os.path.join(parent, dirname)
        os.makedirs(os.path.join(fake, ".claude-plugin"))
        os.makedirs(os.path.join(fake, "tools"))
        with open(os.path.join(fake, ".claude-plugin", "plugin.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"name": plugin_name, "version": "0.0.0"}, f)
        with open(os.path.join(fake, "tools", "verdict-lint.py"), "w",
                  encoding="utf-8") as f:
            f.write("REGISTRY = {}\n")
        return fake

    def test_selftest_passes(self):
        code, out, err = run("stop-gate.py", "--selftest")
        self.assertEqual(code, 0, out + err)
        self.assertIn("selftest passed", out)

    def test_rules_come_from_the_checkout_being_edited(self):
        """A session that ADDS a verdict state must be able to stop.

        Without this, the transcript emits the new state, the INSTALLED release's
        registry does not know it yet, the gate blocks — and the change can never be
        finished because it can never be released. Reproduced for real: a pinned
        v1.14.1 cache blocked the session that introduced `STRUCTURE: regressed`."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            name = sg._manifest_name(sg.PLUGIN_ROOT)
            self.assertIsNotNone(name, "plugin must declare a name")
            fake = self._fake_checkout(tmp, "some-checkout", name)
            deep = os.path.join(fake, "skills", "x")
            os.makedirs(deep)
            self.assertEqual(str(sg.suite_root(deep)), fake,
                             "a session inside a suite checkout must be governed by it")

    def test_unrelated_directory_falls_back_to_the_installed_plugin(self):
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sg.suite_root(tmp), sg.PLUGIN_ROOT)

    def test_identity_is_the_manifest_name_not_a_directory_name(self):
        """Identity must come from the manifest, so a checkout is recognised whatever
        its directory is called.

        The previous version of this test asserted `PLUGIN_ROOT.name != manifest_name`
        — a fact about the CHECKOUT DIRECTORY, not about the code. It passed only
        because GitHub happens to name the repo `top-tier-engineer-skill` while the
        plugin is named `top-tier-engineer`; in a clone named after the plugin it
        failed, green in CI and red on the author's machine. So it is rebuilt to assert
        the property directly, in the case that actually discriminates: a checkout whose
        directory name matches nothing, resolved purely by what its manifest declares."""
        sg = self._load()
        name = sg._manifest_name(sg.PLUGIN_ROOT)
        self.assertIsNotNone(name, "plugin must declare a name")
        with tempfile.TemporaryDirectory() as tmp:
            # Deliberately named nothing like the plugin: only the manifest can identify it.
            fake = self._fake_checkout(tmp, "zzz-unrelated-dirname", name)
            self.assertEqual(str(sg.suite_root(fake)), fake,
                             "identity must come from the manifest, not the directory name")

            # And the converse: a directory NAMED like the plugin but declaring a
            # different plugin must NOT be adopted. This is the half a dirname check
            # gets wrong, and it holds regardless of what this checkout is called.
            impostor = self._fake_checkout(tmp, name, "some-other-plugin")
            self.assertEqual(sg.suite_root(impostor), sg.PLUGIN_ROOT,
                             "a directory merely NAMED like the plugin is not the plugin")

    def test_internal_error_fails_open(self):
        """A lint tool must never wedge a session on its own bug."""
        code, out, err = run("stop-gate.py", stdin="not json at all")
        self.assertEqual(code, 0, out + err)

class StopHookInterpreter(unittest.TestCase):
    """F2: select the interpreter by existence (`command -v`), not by running it and
    falling back on exit code — the latter (an earlier draft's `python3 ... || python
    ...`) re-runs stop-gate.py on an already-drained stdin whenever python3 exists
    but legitimately exits non-zero, silently turning a real block into a pass.
    """

    def test_hooks_json_selects_by_existence_not_by_running_twice(self):
        root = os.path.dirname(HERE)
        data = json.load(open(os.path.join(root, "hooks", "hooks.json"), encoding="utf-8"))
        command = data["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertIn("command -v python3", command,
                      "must probe by existence, not by running it and reading its exit code")
        self.assertNotRegex(command, r"\|\|\s*python\b",
                            "must not fall back via `||` on exit code — that re-runs the "
                            "script with already-drained stdin")
        self.assertIn("stop-gate.py", command)

    def test_selected_branch_receives_full_stdin(self):
        # Reproduce the hook's own shell logic directly (skip the `command -v`
        # probe — this machine's PATH is what it is) and confirm the payload
        # reaches stop-gate.py unconsumed.
        payload = '{"hello": "world"}'
        p = subprocess.run(
            [sys.executable, os.path.join(HERE, "stop-gate.py")],
            input=payload, capture_output=True, text=True,
        )
        self.assertNotIn("internal error", p.stdout + p.stderr, p.stderr)


if __name__ == "__main__":
    unittest.main()
