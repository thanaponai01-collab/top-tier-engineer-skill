#!/usr/bin/env python3
"""stop-gate.py — the Stop hook's own selftest and identity/authority guards."""
import json, os, tempfile, unittest
from _helpers import run, HERE


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
            fake = os.path.join(tmp, "some-checkout")
            os.makedirs(os.path.join(fake, ".claude-plugin"))
            os.makedirs(os.path.join(fake, "tools"))
            name = sg._manifest_name(sg.PLUGIN_ROOT)
            self.assertIsNotNone(name, "plugin must declare a name")
            with open(os.path.join(fake, ".claude-plugin", "plugin.json"), "w",
                      encoding="utf-8") as f:
                json.dump({"name": name, "version": "0.0.0"}, f)
            with open(os.path.join(fake, "tools", "verdict-lint.py"), "w",
                      encoding="utf-8") as f:
                f.write("REGISTRY = {}\n")
            deep = os.path.join(fake, "skills", "x")
            os.makedirs(deep)
            self.assertEqual(str(sg.suite_root(deep)), fake,
                             "a session inside a suite checkout must be governed by it")

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

        `suite_root` matches on a manifest `name` any directory may assert, so
        before this guard two planted files — plugin.json and tools/verdict-lint.py
        — anywhere at or above cwd got their module body exec'd as the user on
        every Stop, silently (the hook fails open). Identity by self-asserted
        string is not authority; code comes from PLUGIN_ROOT alone."""
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

    def test_a_checkouts_new_verdict_state_still_governs_its_session(self):
        """The legitimate case survives the guard: registry read as DATA."""
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

    def test_unrelated_directory_falls_back_to_the_installed_plugin(self):
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sg.suite_root(tmp), sg.PLUGIN_ROOT)

    def test_identity_is_the_manifest_name_not_a_directory_name(self):
        """Install path is <plugin>/<version>/ and the checkout is
        `top-tier-engineer-skill` — neither directory is named what the plugin is
        named, so keying on a directory name silently never matches."""
        sg = self._load()
        self.assertNotEqual(sg.PLUGIN_ROOT.name, sg._manifest_name(sg.PLUGIN_ROOT))

    def test_internal_error_fails_open(self):
        """A lint tool must never wedge a session on its own bug."""
        code, out, err = run("stop-gate.py", stdin="not json at all")
        self.assertEqual(code, 0, out + err)


if __name__ == "__main__":
    unittest.main()
