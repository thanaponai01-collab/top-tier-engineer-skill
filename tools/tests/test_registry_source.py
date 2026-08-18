#!/usr/bin/env python3
"""
_registry_source.py — the one owner of "read a verdict-lint.py's §5 REGISTRY without
executing it", shared by registry-check.py and stop-gate.py.

Part of the suite's own test floor; run them all with `python3 tools/test_tools.py`.
"""
import os, re, tempfile, unittest

from _helpers import HERE, run

import _registry_source as rs


def _write(tmp, body):
    p = os.path.join(tmp, "verdict-lint.py")
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    return p


class RegistrySource(unittest.TestCase):

    def test_reads_the_real_linter(self):
        """The shared reader must agree with the linter it actually ships beside."""
        reg = rs.read(os.path.join(HERE, "verdict-lint.py"))
        self.assertIsInstance(reg, dict)
        self.assertIn("GATE", reg)
        self.assertEqual(reg["GATE"], {"pass", "fail"})

    def test_none_means_nothing_parseable_and_empty_means_declared_empty(self):
        """Callers apply different policies to the two, so they must be distinct:
        registry-check dies on None, stop-gate fails closed to {}."""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(rs.read(_write(tmp, "x = 1\n")))
            self.assertEqual(rs.read(_write(tmp, "REGISTRY = {}\n")), {})
            self.assertIsNone(rs.read(os.path.join(tmp, "does-not-exist.py")))
            self.assertIsNone(rs.read(_write(tmp, "REGISTRY = {\n")))       # syntax error
            self.assertIsNone(rs.read(_write(tmp, "REGISTRY = [1, 2]\n")))  # not a dict

    def test_evaluates_no_code(self):
        """literal_eval only — the whole reason this is not an import."""
        with tempfile.TemporaryDirectory() as tmp:
            canary = os.path.join(tmp, "canary")
            self.assertIsNone(rs.read(_write(
                tmp,
                "import pathlib\n"
                f"REGISTRY = {{'X': pathlib.Path({canary!r}).write_text('x')}}\n")))
            self.assertFalse(os.path.exists(canary))

    def test_annotated_declaration_is_the_same_declaration(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                rs.read(_write(tmp, "REGISTRY: dict = {'A': {'x'}}\n")), {"A": {"x"}})

    def test_module_level_only(self):
        """A REGISTRY inside a function or an `if` is not the module's declaration."""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(rs.read(_write(tmp, "if True:\n    REGISTRY = {'A': {'x'}}\n")))
            self.assertIsNone(rs.read(_write(tmp, "def f():\n    REGISTRY = {'A': {'x'}}\n")))

    def test_non_string_members_are_dropped_not_crashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                rs.read(_write(tmp, "REGISTRY = {'A': {1, 'x', None}, 2: {'y'}}\n")),
                {"A": {"x"}})

    def test_the_two_readers_it_replaced_could_disagree(self):
        """Why one owner, concretely: the regex `registry-check.py` used required
        `REGISTRY = {` at column 0 with a closing brace at column 0, so a declaration
        Python accepts — an annotation, or any other spelling — read as *absent* to one
        tool and *present* to the other. Two answers to "what does this file declare"
        is the divergence D-5 documented one instance earlier."""
        old_regex = re.compile(r"^REGISTRY = \{(.*?)^\}", re.S | re.M)
        annotated = "REGISTRY: dict = {\n    'A': {'x'},\n}\n"
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(old_regex.search(annotated),
                              "the regex reader saw no declaration here")
            self.assertEqual(rs.read(_write(tmp, annotated)), {"A": {"x"}},
                             "the AST reader sees the declaration Python sees")

    def test_both_callers_use_it_and_keep_their_own_error_policy(self):
        """Law 1 is only kept if nobody re-grows a private copy."""
        for tool in ("registry-check.py", "stop-gate.py"):
            src = open(os.path.join(HERE, tool), encoding="utf-8").read()
            # assertTrue, not assertIn: assertIn's failure message pastes the whole
            # file, which buries the one sentence a reader needs.
            self.assertTrue("_registry_source" in src,
                            f"{tool} must read REGISTRY through the shared owner")
            self.assertTrue("ast.literal_eval" not in src,
                            f"{tool} re-grew its own parse of REGISTRY — Law 1, every "
                            f"rule lives in exactly one place, is broken")
        # …and the policies stay different: fatal vs fail-closed.
        code, out, err = run("registry-check.py")
        self.assertEqual(code, 0, out + err)


if __name__ == "__main__":
    unittest.main()
