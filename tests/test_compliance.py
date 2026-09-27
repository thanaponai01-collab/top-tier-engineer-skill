#!/usr/bin/env python3
"""
compliance.py — schema, privacy and guardrail checks that exit 0 or 1.

Run them all with `python -m unittest discover tests`.
"""
import json, os, tempfile, unittest

from _helpers import run
from test_verify import write

SCHEMA = {"type": "object", "required": ["id", "amount"],
          "properties": {"id": {"type": "string", "pattern": "^r_"},
                         "amount": {"type": "number", "minimum": 0},
                         "status": {"enum": ["paid", "refunded"]}}}


def thai_id(first12):
    return first12 + str((11 - sum(int(first12[i]) * (13 - i) for i in range(12)) % 11) % 10)


def put_json(tmp, name, obj):
    write(tmp, name, json.dumps(obj))
    return os.path.join(tmp, name)


class Schema(unittest.TestCase):
    def check(self, data, *flags, schema=SCHEMA):
        with tempfile.TemporaryDirectory() as tmp:
            s, d = put_json(tmp, "s.json", schema), put_json(tmp, "d.json", data)
            return run("compliance.py", "schema", s, d, *flags)

    def test_conforming_output_passes_and_each_violation_fails(self):
        self.assertEqual(self.check({"id": "r_1", "amount": 5, "status": "paid"})[0], 0)
        for bad, needle in [({"amount": 5}, "missing required field 'id'"),
                            ({"id": "x_1", "amount": 5}, "does not match"),
                            ({"id": "r_1", "amount": -1}, "minimum"),
                            ({"id": "r_1", "amount": True}, "expected number"),
                            ({"id": "r_1", "amount": 1, "status": "lost"}, "is not one of")]:
            code, out, _ = self.check(bad)
            self.assertEqual(code, 1, out)
            self.assertIn(needle, out)

    def test_strict_closes_objects_and_default_does_not(self):
        extra = {"id": "r_1", "amount": 5, "card": "4111"}
        self.assertEqual(self.check(extra)[0], 0)
        code, out, _ = self.check(extra, "--strict")
        self.assertEqual(code, 1)
        self.assertIn("unexpected field 'card'", out)

    def test_a_keyword_it_cannot_check_is_an_error_not_a_pass(self):
        code, out, _ = self.check({"id": "r_1"}, schema={"type": "object", "dependentRequired": {"id": ["x"]}})
        self.assertEqual(code, 2, out)
        self.assertIn("unsupported keyword", out)

    def test_nested_ref_and_items(self):
        sch = {"type": "array", "items": {"$ref": "#/$defs/row"},
               "$defs": {"row": {"type": "object", "required": ["n"], "additionalProperties": False,
                                 "properties": {"n": {"type": "integer"}}}}}
        self.assertEqual(self.check([{"n": 1}, {"n": 2}], schema=sch)[0], 0)
        code, out, _ = self.check([{"n": 1}, {"n": 1.5}], schema=sch)
        self.assertEqual(code, 1)
        self.assertIn("$[1].n", out)


class Privacy(unittest.TestCase):
    def scan(self, text, *flags):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "out/a.txt", text)
            return run("compliance.py", "privacy", tmp, *flags)

    def test_each_kind_is_caught_and_the_value_is_never_printed(self):
        secrets = {"email": "mail bob@example.com now", "card number": "card 4111 1111 1111 1111",
                   "national id (TH)": f"id {thai_id('110170023067')}",
                   "aws access key": "AKIAABCDEFGHIJKLMNOP", "private key": "-----BEGIN RSA PRIVATE KEY-----",
                   "secret assignment": "password = hunter2hunter2"}
        for kind, text in secrets.items():
            code, out, _ = self.scan(text)
            self.assertEqual(code, 1, (kind, out))
            self.assertIn(kind, out)
            for frag in ("bob@example.com", "4111 1111", "hunter2", "AKIAABC"):
                self.assertNotIn(frag, out)

    def test_clean_text_and_look_alikes_pass(self):
        code, out, _ = self.scan("order 4111111111111112 total 12\nversion 1.2.3\nhello")
        self.assertEqual(code, 0, out)

    def test_allow_accepts_a_known_match(self):
        self.assertEqual(self.scan("ping support@example.com")[0], 1)
        self.assertEqual(self.scan("ping support@example.com", "--allow", "support@example.com")[0], 0)

    def test_scanning_nothing_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run("compliance.py", "privacy", tmp)[0], 2)


class Guardrail(unittest.TestCase):
    ECHO = ["--", "python", "-c",
            "import sys; t=sys.stdin.read(); sys.exit(3) if 'rm -rf' in t else print('ok:'+t)"]

    def test_holds_when_every_case_is_refused_and_fails_when_one_slips(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = put_json(tmp, "good.json", [{"name": "shell", "stdin": "rm -rf /", "exit": "nonzero"},
                                               {"name": "benign", "stdin": "hi", "must_match": ["ok:hi"], "exit": 0}])
            code, out, _ = run("compliance.py", "guardrail", good, *self.ECHO)
            self.assertEqual(code, 0, out)
            leak = put_json(tmp, "leak.json", [{"name": "leak", "stdin": "hi", "must_not_match": ["ok:"]}])
            code, out, _ = run("compliance.py", "guardrail", leak, *self.ECHO)
            self.assertEqual(code, 1)
            self.assertIn("FAIL  leak", out)

    def test_no_cases_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run("compliance.py", "guardrail", put_json(tmp, "e.json", []), *self.ECHO)[0], 2)


class Repeat(unittest.TestCase):
    def test_identical_output_passes_and_a_varying_one_fails(self):
        self.assertEqual(run("compliance.py", "repeat", "3", "--", "python", "-c", "print('same')")[0], 0)
        code, out, _ = run("compliance.py", "repeat", "3", "--", "python", "-c", "import os; print(os.urandom(4).hex())")
        self.assertEqual(code, 1, out)
        self.assertIn("differs from run 1", out)


if __name__ == "__main__":
    unittest.main()
