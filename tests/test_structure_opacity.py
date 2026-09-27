#!/usr/bin/env python3
"""
structure_opacity.py — the opacity/shape measurement itself, tested directly.

test_structure_report.py already exercises this module end-to-end through the
CLI, but only the composed outcome (a finding or none). These tests pin down
the individual functions the report is built from, so a change to one of them
fails here instead of only showing up as a mysterious shift in someone else's
CLI assertion.

Run them all with `python -m unittest discover tests`.
"""
import os, sys, unittest

from _helpers import ROOT

SCRIPTS = os.path.join(ROOT, "skills", "structure-gate", "scripts")
sys.path.insert(0, SCRIPTS)

import structure_opacity as opacity  # noqa: E402  - imported after the path is set


class ContiguousSpans(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(opacity.contiguous_spans(set()), [])

    def test_single_run(self):
        self.assertEqual(opacity.contiguous_spans({1, 2, 3}), [(1, 3)])

    def test_gap_splits_into_two_runs(self):
        self.assertEqual(opacity.contiguous_spans({1, 2, 5, 6, 7}), [(1, 2), (5, 7)])

    def test_minimum_filters_short_runs(self):
        self.assertEqual(opacity.contiguous_spans({1, 2, 10, 11, 12, 13}, minimum=3),
                          [(10, 13)])

    def test_unsorted_input_is_handled(self):
        self.assertEqual(opacity.contiguous_spans({7, 6, 5, 1, 2}), [(1, 2), (5, 7)])


class PythonOpaqueLines(unittest.TestCase):
    def test_plain_code_has_no_opaque_lines(self):
        opaque, docs = opacity.python_opaque_lines("def add(a, b):\n    return a + b\n")
        self.assertEqual(opaque, set())
        self.assertEqual(docs, set())

    def test_value_string_on_its_own_line_is_opaque(self):
        src = 'x = 1\nPAGE = """\nhidden content here\n"""\n'
        opaque, _ = opacity.python_opaque_lines(src)
        self.assertIn(3, opaque)
        self.assertNotIn(1, opaque)

    def test_string_sharing_a_line_with_code_is_not_opaque(self):
        # `x = "short"` — the analyzer entered this line, it is not a blind spot.
        opaque, _ = opacity.python_opaque_lines('x = "short"\n')
        self.assertEqual(opaque, set())

    def test_module_docstring_is_documented_not_opaque(self):
        src = '"""\nAn ordinary module docstring.\n"""\n\n\ndef f():\n    return 1\n'
        opaque, docs = opacity.python_opaque_lines(src)
        self.assertEqual(opaque, set())
        self.assertIn(2, docs)

    def test_comment_is_documented(self):
        opaque, docs = opacity.python_opaque_lines("# a comment\nx = 1\n")
        self.assertEqual(opaque, set())
        self.assertIn(1, docs)

    def test_unparseable_source_returns_none(self):
        self.assertIsNone(opacity.python_opaque_lines("def f(:\n    this is not python\n"))


class ShapeStats(unittest.TestCase):
    def test_empty_text(self):
        stats = opacity.shape_stats("")
        self.assertEqual(stats["lines"], 0)
        self.assertEqual(stats["score"], 0)

    def test_uniform_prose_is_low_signal(self):
        text = "\n".join(f"This is paragraph {i} of ordinary prose." for i in range(50))
        stats = opacity.shape_stats(text)
        self.assertFalse(opacity.is_code_shaped(stats))

    def test_nested_irregular_code_is_high_signal(self):
        lines = ["function outer() {"]
        for i in range(20):
            lines += [f"  if (x > {i}) {{", f"    doThing{i}();", "  }"]
        lines.append("}")
        stats = opacity.shape_stats("\n".join(lines))
        self.assertGreaterEqual(stats["indent_levels"], 3)
        self.assertTrue(opacity.is_code_shaped(stats))

    def test_flat_data_has_low_indent_variety(self):
        text = "\n".join(f"US,United States,{i},840" for i in range(50))
        stats = opacity.shape_stats(text)
        self.assertFalse(opacity.is_code_shaped(stats))


class IsCodeShaped(unittest.TestCase):
    def test_single_criterion_is_not_enough(self):
        # High irregularity alone (length_cv) without nesting must not flag.
        stats = {"indent_levels": 1, "length_cv": 0.9, "max_line": 10, "score": 1, "lines": 5}
        self.assertFalse(opacity.is_code_shaped(stats))

    def test_both_criteria_flags(self):
        stats = {"indent_levels": 4, "length_cv": 0.5, "max_line": 10, "score": 2, "lines": 5}
        self.assertTrue(opacity.is_code_shaped(stats))

    def test_minified_line_flags_regardless_of_score(self):
        stats = {"indent_levels": 1, "length_cv": 0.0, "max_line": 501, "score": 0, "lines": 1}
        self.assertTrue(opacity.is_code_shaped(stats))


class LooksLike(unittest.TestCase):
    def test_markup_is_detected(self):
        self.assertIn("markup", opacity.looks_like("<div><script>x()</script></div>"))

    def test_sql_is_detected(self):
        self.assertIn("sql", opacity.looks_like("SELECT * FROM users WHERE id = 1"))

    def test_unrecognized_when_no_hint_matches(self):
        self.assertEqual(opacity.looks_like("proc handle ~ (state) -> yield state"),
                          ["unrecognized"])

    def test_never_used_to_decide_flagging(self):
        # A blob that would be labeled "unrecognized" must still be measured by
        # shape alone, independent of looks_like's guess.
        lines = []
        for i in range(40):
            lines += [f"proc handle{i} ~ (state, opts) ->",
                      "    when state?kind == 'lap' ->",
                      "        loop [item <- state?rows] ->",
                      "            yield item?total := item?s1 |+| item?s2",
                      "    otherwise -> nil"]
        text = "\n".join(lines)
        self.assertEqual(opacity.looks_like(text), ["unrecognized"])
        stats = opacity.shape_stats(text)
        self.assertTrue(opacity.is_code_shaped(stats))


class Measure(unittest.TestCase):
    def test_unsupported_extension_reports_unsupported_not_clean(self):
        result = opacity.measure("file.rb", "def f\n  puts 'x'\nend\n", min_span=1)
        self.assertFalse(result["supported"])
        self.assertEqual(result["opaque"], 0)
        self.assertEqual(result["spans"], [])

    def test_no_extension_reports_unsupported(self):
        result = opacity.measure("Makefile", "all:\n\techo hi\n", min_span=1)
        self.assertFalse(result["supported"])

    def test_unparseable_python_reports_unsupported(self):
        result = opacity.measure("bad.py", "def f(:\n", min_span=1)
        self.assertFalse(result["supported"])

    def test_supported_clean_file_has_full_coverage(self):
        src = "def add(a, b):\n    return a + b\n"
        result = opacity.measure("ok.py", src, min_span=1)
        self.assertTrue(result["supported"])
        self.assertEqual(result["opaque"], 0)
        self.assertEqual(result["spans"], [])
        self.assertEqual(result["total"], len(src.splitlines()))

    def test_short_opaque_run_below_min_span_is_not_a_span(self):
        src = 'x = 1\nY = """\nonly one line\n"""\n'
        result = opacity.measure("short.py", src, min_span=5)
        self.assertEqual(result["spans"], [])
        # still counted toward opacity even though it's below the reportable span size
        self.assertGreater(result["opaque"], 0)

    def test_code_shaped_opaque_span_is_reported(self):
        body = ["<script>"]
        for i in range(30):
            body += [f"function f{i}(x) {{", f"  if (x > {i}) {{", "    return x + 1;", "  }", "}"]
        body.append("</script>")
        src = 'import json\n\nPAGE = """' + "\n".join(body) + '"""\n'
        result = opacity.measure("hidden.py", src, min_span=1)
        self.assertTrue(result["supported"])
        self.assertEqual(len(result["spans"]), 1)
        self.assertIn("js", result["spans"][0]["hint"])


if __name__ == "__main__":
    unittest.main()
