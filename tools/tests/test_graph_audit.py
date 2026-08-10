#!/usr/bin/env python3
"""graph-audit.py — the no-symptom sweep: dead modules, unused defs, layer breaches."""
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

    def _clean_tree(self, tmp):
        """Two modules, one importing the other, no dead modules and no defs at all —
        so the layer dimension is the only thing a verdict can be about."""
        with open(os.path.join(tmp, "main.py"), "w", encoding="utf-8") as f:
            f.write("import helper\nVALUE = helper.NAME\n")
        with open(os.path.join(tmp, "helper.py"), "w", encoding="utf-8") as f:
            f.write('NAME = "x"\n')

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

    def test_empty_tree_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("graph-audit.py", tmp)
            self.assertEqual(code, 2, out)
            self.assertIn("blocked(no analyzable source)", out)

    def test_layer_spec_matching_nothing_is_unknown_not_clean(self):
        """PROTOCOL §10 rule 5: unmeasured must never render as clean.

        A layer spec whose prefixes match no module in the tree checked
        nothing; before this test the report said '(proven) — clean'."""
        with tempfile.TemporaryDirectory() as tmp:
            # A tree with NO other findings, so the layer dimension is the only thing
            # the verdict can be about. (Real findings rightly outrank an unmeasured
            # dimension — that precedence is deliberate, so it must not be under test
            # here.)
            self._clean_tree(tmp)
            bogus = os.path.join(tmp, "bogus-layers.txt")
            with open(bogus, "w", encoding="utf-8") as fh:
                fh.write("alpha: no/such/pkg/\nbeta: other/absent/\n")
            code, out, err = run("graph-audit.py", tmp, "--layers", bogus)
            self.assertIn("UNKNOWN", out, out + err)
            self.assertNotIn("clean against declared", out)
            # The VERDICT LINE and EXIT CODE are the channels automation reads
            # (PROTOCOL §5). Honesty in the prose alone is the same defect one
            # channel over — CI and run-trace.py never see the paragraph.
            self.assertNotIn("LATENT: clean", out)
            self.assertIn("LATENT: blocked(layer spec matched 0 of 2", out)
            self.assertEqual(code, 2, out)

    def test_a_layers_file_that_parses_to_nothing_is_not_reported_as_absent(self):
        """`--layers` WAS passed; blaming the operator for not passing it hides it."""
        with tempfile.TemporaryDirectory() as tmp:
            self._clean_tree(tmp)
            empty = os.path.join(tmp, "empty-layers.txt")
            with open(empty, "w", encoding="utf-8") as fh:
                fh.write("# only a comment\n\n")
            code, out, _ = run("graph-audit.py", tmp, "--layers", empty)
            self.assertNotIn("no --layers file declared", out)
            self.assertIn("parsed to zero layers", out)
            self.assertEqual(code, 2, out)

    def test_layer_coverage_is_always_reported(self):
        """Coverage is reported even when the spec matches everything."""
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp)
            code, out, err = run("graph-audit.py", tmp, "--layers", layers)
            self.assertIn("coverage:", out, out + err)
            self.assertIn("modules classified", out)
            jcode, jout, _ = run("graph-audit.py", tmp, "--layers", layers,
                                 "--json")
            cov = json.loads(jout)["layer_coverage"]
            self.assertEqual(cov["total"], 5, jout)
            self.assertLess(cov["mapped"], cov["total"])   # main.py unmapped


if __name__ == "__main__":
    unittest.main()
