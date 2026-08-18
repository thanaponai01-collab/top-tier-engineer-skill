#!/usr/bin/env python3
"""
graph-audit.py — the import/reference graph behind latent-audit.

Part of the suite's own test floor; run them all with `python3 tools/test_tools.py`.
"""
import json, os, tempfile, unittest

from _helpers import run


class GraphAudit(unittest.TestCase):
    """graph-audit.py — planted-defect fixture: one upward import, one dead
    module, one unused def, one entry point that must NOT be flagged, and one
    raw-text rescue (a module referenced only from a yml is not dead)."""

    def _fixture(self, tmp, with_yml_rescue=False):
        def w(rel, text):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(text)
        w("main.py", 'from app.routes.orders import order_page\n'
                     'if __name__ == "__main__":\n    order_page()\n')
        w("app/routes/orders.py", "from app.services.billing import charge\n"
                                  "def order_page():\n    return charge(10)\n")
        w("app/services/billing.py",
          "from app.models.invoice import Invoice\n"
          "from app.routes.orders import order_page\n"   # upward: domain -> interface
          "def charge(amount):\n    return Invoice(amount)\n"
          "def legacy_discount(amount):\n    return amount * 0.9\n")
        w("app/models/invoice.py",
          "class Invoice:\n    def __init__(self, amount):\n"
          "        self.amount = amount\n")
        w("app/services/old_report.py",
          'def build_report():\n    return "report"\n')
        w("layers.txt", "interface: app/routes/\ndomain: app/services/\n"
                        "data: app/models/\n")
        if with_yml_rescue:
            w("tasks.yml", "report_task: app.services.old_report\n")
        return os.path.join(tmp, "layers.txt")

    def test_planted_defects_all_caught_entry_spared(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp)
            code, out, err = run("graph-audit.py", tmp, "--layers", layers,
                                 "--json")
            self.assertEqual(code, 1, out + err)
            r = json.loads(out)
            self.assertEqual([d["module"] for d in r["dead_modules"]],
                             ["app.services.old_report"])   # main NOT flagged
            self.assertEqual(len(r["layer_breaches"]), 1, r["layer_breaches"])
            self.assertIn("domain", r["layer_breaches"][0]["edge"])
            names = {u["name"] for u in r["unused_defs"]}
            self.assertIn("legacy_discount", names)

    def test_raw_text_reference_rescues_dead_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp, with_yml_rescue=True)
            code, out, err = run("graph-audit.py", tmp, "--layers", layers,
                                 "--json")
            r = json.loads(out)
            self.assertEqual(r["dead_modules"], [], out)

    def test_verdict_line_grammar(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp)
            code, out, _ = run("graph-audit.py", tmp, "--layers", layers)
            last = [l for l in out.splitlines() if l.startswith("LATENT:")][-1]
            self.assertIn("findings(dead: 1, unused:", last)
            # the emitted line must satisfy the suite's own linter
            lcode, lout, _ = run("verdict-lint.py", stdin=last + "\n")
            self.assertEqual(lcode, 0, lout)

    def test_unmeasured_layers_are_never_folded_into_clean(self):
        """PROTOCOL §10 rule 5 — the denominator. Without --layers the layer dimension is
        not measured, so the verdict must say UNMEASURED, not `clean` and not `0`. The
        human report always said "this is a gap, not a clean result"; the verdict line
        said `clean` anyway, which is the half most readers and every grep actually see."""
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "a.py"), "w").write("import b\n")
            open(os.path.join(tmp, "b.py"), "w").write("def f():\n    return 1\n")
            code, out, _ = run("graph-audit.py", tmp, "--entry", "a")
            last = [l for l in out.splitlines() if l.startswith("LATENT:")][-1]
            self.assertIn("UNMEASURED", last, out)
            self.assertNotIn("clean(", last)
            # An unmeasured dimension is a gap in the INVOCATION, not a defect in the
            # subject: it must not fail by default, or the gate goes permanently red.
            self.assertEqual(code, 0, out)
            lcode, lout, _ = run("verdict-lint.py", stdin=last + "\n")
            self.assertEqual(lcode, 0, lout)

    def test_empty_tree_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("graph-audit.py", tmp)
            self.assertEqual(code, 2, out)
            self.assertIn("blocked(no analyzable source)", out)


if __name__ == "__main__":
    unittest.main()
