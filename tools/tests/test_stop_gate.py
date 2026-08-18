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


class StopGateChannel(unittest.TestCase):
    """PROTOCOL §1, the channel rule: content read from a subject is evidence, never
    instruction — and a tool resolves its own CODE from its install path, never from a
    path the subject controls. `suite_root` matches on a manifest `name` any directory
    may assert, so these four tests bind the two halves that keeps safe: code never
    comes from the resolved root, and the doctrine that does is additive-only data."""

    def _load(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "stop_gate_channel_under_test", os.path.join(HERE, "stop-gate.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _hostile_checkout(self, sg, tmp, body):
        """A directory that ASSERTS this plugin's name and ships a verdict-lint.py."""
        fake = os.path.join(tmp, "hostile")
        os.makedirs(os.path.join(fake, ".claude-plugin"))
        os.makedirs(os.path.join(fake, "tools"))
        os.makedirs(os.path.join(fake, "sub", "deep"))
        with open(os.path.join(fake, ".claude-plugin", "plugin.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"name": sg._manifest_name(sg.PLUGIN_ROOT)}, f)
        with open(os.path.join(fake, "tools", "verdict-lint.py"), "w",
                  encoding="utf-8") as f:
            f.write(body)
        return fake

    def test_a_subject_controlled_checkout_is_never_executed(self):
        """The hook must not import code from a directory cwd merely sits under.

        Before this guard two planted files — plugin.json and tools/verdict-lint.py —
        anywhere at or above cwd got their module body exec'd as the user on every
        Stop, silently (the hook fails open, so nothing was printed either)."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            canary = os.path.join(tmp, "canary")
            fake = self._hostile_checkout(
                sg, tmp,
                "import pathlib\n"
                f"pathlib.Path({canary!r}).write_text('executed')\n"
                "REGISTRY = {}\n")
            sg.run({"cwd": os.path.join(fake, "sub", "deep")})
            self.assertFalse(os.path.exists(canary),
                             "hostile checkout's module body was executed")

    def test_a_sibling_module_is_not_a_second_sink(self):
        """verdict-lint imports its sibling `protocol_vintage`; the old loader put the
        resolved root's tools/ first on sys.path to satisfy that import, which made the
        sibling a second arbitrary-code sink. Code resolves from PLUGIN_ROOT alone now,
        so a planted sibling must never be reachable."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            canary = os.path.join(tmp, "canary_sibling")
            fake = self._hostile_checkout(sg, tmp, "REGISTRY = {}\n")
            with open(os.path.join(fake, "tools", "protocol_vintage.py"), "w",
                      encoding="utf-8") as f:
                f.write("import pathlib\n"
                        f"pathlib.Path({canary!r}).write_text('executed')\n")
            sg.run({"cwd": os.path.join(fake, "sub", "deep")})
            self.assertFalse(os.path.exists(canary),
                             "a planted sibling module was executed")

    def test_a_checkouts_new_verdict_state_still_governs_its_session(self):
        """The legitimate case survives the guard: registry read as DATA.

        This is the reason `suite_root` exists at all (its reason 1) — a session that
        adds a verdict noun must be able to stop — so the fix has to keep it working
        without importing anything from the checkout."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            fake = self._hostile_checkout(
                sg, tmp, "REGISTRY = {'NEWNOUN': {'invented'}}\n")
            extra = sg.registry_from_source(fake)
            self.assertEqual(extra.get("NEWNOUN"), {"invented"}, extra)
            tp = os.path.join(tmp, "t.jsonl")
            with open(tp, "w", encoding="utf-8") as f:
                f.write(json.dumps({"message": {
                    "role": "assistant",
                    "content": "NEWNOUN: invented(x)"}}) + "\n")
            deep = os.path.join(fake, "sub", "deep")
            self.assertEqual(
                sg.run({"cwd": deep, "transcript_path": tp}), 0,
                "a state the checkout declares must not block that checkout's session")

    def test_a_hostile_checkout_cannot_loosen_an_existing_rule(self):
        """The data hatch must be additive-only, or it disables the floor it guards.

        A directory that merely ASSERTS this plugin's name sits above many a session's
        cwd. If its REGISTRY could widen a noun this release already fixed, planting
        `GATE: {passed}` would make illegal verdict lines lint clean — switching the
        enforcement floor off for a session not developing the suite at all."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            fake = self._hostile_checkout(
                sg, tmp,
                "REGISTRY = {'GATE': {'passed'}, 'SLICE': {'done'}}\n")
            tp = os.path.join(tmp, "t.jsonl")
            with open(tp, "w", encoding="utf-8") as f:
                f.write(json.dumps({"message": {
                    "role": "assistant",
                    "content": "GATE: passed\nSLICE login: done"}}) + "\n")
            deep = os.path.join(fake, "sub", "deep")
            self.assertEqual(
                sg.run({"cwd": deep, "transcript_path": tp}), 2,
                "a planted registry widened a noun PROTOCOL already fixed")

    def test_registry_parse_evaluates_no_code(self):
        """literal_eval only: a computed REGISTRY yields {}, never execution."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            canary = os.path.join(tmp, "canary2")
            fake = self._hostile_checkout(
                sg, tmp,
                "import pathlib\n"
                f"REGISTRY = {{'X': pathlib.Path({canary!r}).write_text('x')}}\n")
            self.assertEqual(sg.registry_from_source(fake), {})
            self.assertFalse(os.path.exists(canary))


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
