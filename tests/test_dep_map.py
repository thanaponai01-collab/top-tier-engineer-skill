#!/usr/bin/env python3
"""
dep-map.py — the shape readings behind arch-design (cycles, hubs, pass-through, seams, I/O).

It reads the graph that graph-audit.py writes with --edges, so these tests build a small tree,
write the graph with the real graph-audit.py, and read it back. Every reading has a decoy that
looks like it and must not be flagged.

Run them all with `python -m unittest discover tests`.
"""
import json, os, tempfile, unittest

from _helpers import run, ROOT


def write(tmp, rel, text):
    p = os.path.join(tmp, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


class DepMap(unittest.TestCase):
    def read(self, tree, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in tree.items():
                write(tmp, rel, text)
            edges = os.path.join(tmp, "edges.json")
            run("graph-audit.py", tmp, "--edges", edges)
            code, out, err = run("dep-map.py", edges, "--json", *extra)
            self.assertEqual(code, 0, out + err)
            return json.loads(out)

    def test_cycle_found_and_acyclic_chain_not(self):
        r = self.read({
            "a.py": "import b\n\ndef f():\n    return b.g()\n",
            "b.py": "import c\n\ndef g():\n    return c.h()\n",
            "c.py": "import a\n\ndef h():\n    return a.f()\n",
            "d.py": "import e\n\ndef k():\n    return e.m()\n",
            "e.py": "def m():\n    return 1\n",
        })
        self.assertEqual([c["modules"] for c in r["cycles"]], [["a", "b", "c"]])
        self.assertEqual(len(r["cycles"][0]["edges"]), 3)

    def test_hub_stability_separates_leaf_from_risky(self):
        tree = {"leaf.py": "def util():\n    return 1\n",
                "mid.py": ("import leaf\n" + "".join(f"import dep{i}\n" for i in range(5))
                           + "\ndef m():\n    return leaf.util()\n")}
        for i in range(5):
            tree[f"dep{i}.py"] = "def d():\n    return 1\n"
        for i in range(6):
            tree[f"user{i}.py"] = "import leaf\nimport mid\n\ndef f():\n    return leaf.util() + mid.m()\n"
        hubs = {h["module"]: h for h in self.read(tree)["hubs"]}
        self.assertEqual(hubs["leaf"]["instability"], 0.0)      # imports nothing: stable
        self.assertFalse(hubs["leaf"]["risky"])                  # high fan-in alone is not a defect
        self.assertTrue(hubs["mid"]["risky"])                    # imported by 6, imports leaf

    def test_pass_through_flagged_but_transforming_wrapper_is_not(self):
        r = self.read({
            "core.py": "def work(a, b):\n    return a + b\n",
            "thin.py": "import core\n\ndef work(a, b):\n    return core.work(a, b)\n",
            "shaper.py": "import core\n\ndef work(a, b):\n    return core.work(a.strip(), b)\n",
            "mixed.py": "import core\n\ndef work(a, b):\n    return core.work(a, b)\n\ndef other(a):\n    return a * 2\n",
        })
        self.assertEqual([p["module"] for p in r["pass_through"]], ["thin"])

    def test_seam_count_one_is_hypothetical_two_is_real_structural_counts(self):
        r = self.read({
            "ports.py": ("from typing import Protocol\n\n"
                         "class Sender(Protocol):\n    def send(self, x): ...\n\n"
                         "class Store(Protocol):\n    def save(self, x): ...\n"),
            "smtp.py": "class Smtp:\n    def send(self, x):\n        return x\n",
            "fake.py": "class FakeSender:\n    def send(self, x):\n        return x\n",
            "disk.py": "class Disk:\n    def save(self, x):\n        return x\n",
        })
        seams = {s["seam"]: s for s in r["seams"]}
        self.assertEqual(seams["Sender"]["verdict"], "real")
        self.assertEqual(len(seams["Sender"]["implementers"]), 2)
        self.assertEqual(seams["Store"]["verdict"], "hypothetical")

    def test_io_library_found_and_plain_stdlib_is_not(self):
        r = self.read({
            "fetch.py": "import urllib.request\n\ndef get(u):\n    return urllib.request.urlopen(u)\n",
            "orm.py": "from sqlalchemy.orm import Session\n\ndef open_session():\n    return Session()\n",
            "pure.py": "import json\nimport os.path\n\ndef f(x):\n    return json.dumps(x)\n",
        })
        self.assertEqual([i["module"] for i in r["io"]], ["fetch", "orm"])   # submodule imports count

    def test_cochange_pair_without_import_edge_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in {"billing/a.py": "import shared\n\ndef f():\n    return shared.x\n",
                              "shared.py": "x = 1\n",
                              "reports/b.py": "def g():\n    return 2\n"}.items():
                write(tmp, rel, text)
            edges = os.path.join(tmp, "edges.json")
            run("graph-audit.py", tmp, "--edges", edges)
            change = os.path.join(tmp, "change.json")
            with open(change, "w") as f:
                json.dump({"coupled": [
                    {"a": "billing/a.py", "b": "shared.py", "shared": 5, "confidence": 1.0},
                    {"a": "billing/a.py", "b": "reports/b.py", "shared": 4, "confidence": 0.9}]}, f)
            code, out, err = run("dep-map.py", edges, "--cochange", change, "--json")
            self.assertEqual(code, 0, out + err)
            rows = {(c["a"], c["b"]): c["import_edge"] for c in json.loads(out)["cochange"]}
            self.assertTrue(rows[("billing/a.py", "shared.py")])          # an import explains it
            self.assertFalse(rows[("billing/a.py", "reports/b.py")])      # nothing explains it

    def test_unreadable_graph_is_blocked_not_a_crash(self):
        code, out, _ = run("dep-map.py", os.path.join(tempfile.gettempdir(), "no-such-graph.json"))
        self.assertEqual(code, 2)
        self.assertIn("blocked", out)

    def test_eval_fixture_gives_exactly_the_planted_answer(self):
        """The 40-module eval fixture: one cycle, one pass-through, one real seam, one I/O module,
        and core.util is a stable hub with 16 importers that must not be called risky."""
        fixture = os.path.join(ROOT, "evals", "cases", "arch-design-graph-shape", "fixture")
        with tempfile.TemporaryDirectory() as tmp:
            edges = os.path.join(tmp, "edges.json")
            run("graph-audit.py", fixture, "--edges", edges)
            code, out, err = run("dep-map.py", edges, "--json")
            self.assertEqual(code, 0, out + err)
            r = json.loads(out)
        self.assertEqual([c["modules"] for c in r["cycles"]],
                         [["notifications.email", "orders.status", "shipping.tracking"]])
        self.assertEqual([p["module"] for p in r["pass_through"]], ["services.order_service"])
        self.assertEqual([(s["seam"], s["verdict"]) for s in r["seams"]], [("PaymentGateway", "real")])
        self.assertEqual([i["module"] for i in r["io"]], ["pricing.quote"])
        util = next(h for h in r["hubs"] if h["module"] == "core.util")
        self.assertEqual((util["fan_in"], util["risky"]), (16, False))
        self.assertEqual(r["modules"], 40)


if __name__ == "__main__":
    unittest.main()
