#!/usr/bin/env python3
"""
The suite gating itself: doc/code agreement, the §6 extraction floor, ledger
hygiene, the shared encoding guard, and skill frontmatter budgets.

Part of the suite's own test floor; run them all with `python3 tools/test_tools.py`.
"""
import json, os, re, subprocess, sys, unittest

from _helpers import HERE, run


class SuiteConsistency(unittest.TestCase):
    """The suite's self-description must match the filesystem. A current-state doc
    that names the skill count as a word (PROTOCOL, the plugin manifest) must use the
    word matching the number of skills/ dirs. Earned: 'eighteen skills' shipped into
    PROTOCOL §title while the suite had nineteen — the drift-arbiter file drifted."""

    WORDS = {16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
             20: "twenty", 21: "twenty-one", 22: "twenty-two"}

    # Every pure current-state surface that states the count. README is excluded on
    # purpose: it mixes current and historical counts ("seventeenth skill" narrates a
    # past milestone), so a strict no-neighbour check would false-fail on real history.
    SURFACES = ("PROTOCOL.md", "MAP.md",
                os.path.join(".claude-plugin", "plugin.json"),
                os.path.join(".claude-plugin", "marketplace.json"))

    def test_skill_count_matches_current_state_claims(self):
        root = os.path.dirname(HERE)
        n = sum(1 for e in os.scandir(os.path.join(root, "skills")) if e.is_dir())
        self.assertIn(n, self.WORDS, f"extend WORDS past {n} skills")
        right = self.WORDS[n]
        for rel in self.SURFACES:
            text = open(os.path.join(root, rel), encoding="utf-8").read().lower()
            self.assertIn(right, text, f"{rel} never states the {right}-skill count")
            # Phrasing-independent: a neighbour count word anywhere in a current-state
            # surface is drift, whether it reads "eighteen skills" or "eighteen wired
            # engineering skills". (The bug that shipped was the former; the manifests
            # use the latter, which an adjacency-only check would miss.)
            for k in (n - 1, n + 1):
                self.assertNotIn(self.WORDS[k], text,
                                 f"{rel} names {self.WORDS[k]}; filesystem has {n} skills")

class TestExtractionFloor(unittest.TestCase):
    """PROTOCOL §6 — the degradation rule, mechanically.

    §6 requires every skill to carry the canonical evidence-tag gloss "copied verbatim so
    glosses cannot drift apart", because a skill read alone — vendored, pasted into a prompt,
    copied into another suite — is a real deployment, and without the gloss it keeps its
    vocabulary and loses its constitution.

    Nothing checked this, and it had drifted: at v1.16.1 EIGHT of the nineteen skills carried
    no gloss at all. That is the suite's own §8.1 lesson unapplied to itself — "prefer a
    structural separation you cannot fake over a marker you can" — so here is the structure.
    """

    @staticmethod
    def _norm(s):
        """Whitespace-normalized, blockquote-stripped. A gloss line-wrapped across three
        lines of a markdown blockquote is still verbatim; only the WORDS may not drift."""
        s = re.sub(r'(?m)^[\s>]*', ' ', s)
        return re.sub(r'\s+', ' ', s).strip()

    def _canonical(self):
        root = os.path.dirname(HERE)
        proto = open(os.path.join(root, "PROTOCOL.md"), encoding="utf-8").read()
        m = re.search(r'\(Gloss:.*?log it\.\)', proto, re.S)
        self.assertIsNotNone(m, "PROTOCOL.md §6 no longer contains the canonical gloss")
        return self._norm(m.group(0))

    def test_every_skill_carries_the_canonical_gloss_verbatim(self):
        root = os.path.dirname(HERE)
        canonical = self._canonical()
        missing, drifted = [], []
        skills = sorted(e.name for e in os.scandir(os.path.join(root, "skills")) if e.is_dir())
        self.assertTrue(skills, "no skills found — the check would pass vacuously")
        for name in skills:
            text = open(os.path.join(root, "skills", name, "SKILL.md"), encoding="utf-8").read()
            m = re.search(r'\(Gloss:.*?log it\.\)', text, re.S)
            if not m:
                missing.append(name)
            elif self._norm(m.group(0)) != canonical:
                drifted.append(name)
        self.assertEqual([], missing,
                         "PROTOCOL §6: these skills carry no evidence-tag gloss, so extracting "
                         "one costs it the vocabulary its own rules are written in: "
                         + ", ".join(missing))
        self.assertEqual([], drifted,
                         "PROTOCOL §6: gloss text differs from PROTOCOL.md's canonical copy "
                         "(it is copied verbatim precisely so glosses cannot drift apart): "
                         + ", ".join(drifted))

class RunLedgerRedaction(unittest.TestCase):
    """DECISION_LEDGER D004 — the run ledger ships in a PUBLIC repo, redacted.

    D004 created a standing obligation ("every future run added to `runs/` must be redacted
    before it is committed") on an explicitly ONE-WAY door: publication cannot be undone.
    It was prose only, which this suite's own §8.1 calls the weak form — "prefer a structure
    you cannot fake over a marker you can". This is the structure. It is a floor, not proof
    of anonymity: it catches the identifiers a past run actually leaked and the shape of a
    local path, not correlation by a reader who already knows the director's projects.
    """

    # Subject identities retired by the v1.17.0 redaction. A new run naming one of these has
    # re-introduced an identity the project decided not to publish.
    RETIRED = ("tickit", "timetracker", "tier-memory", "tier_memory",
               "flask_ticket_booking_system")
    # Absolute local paths: Windows drive-letter or POSIX home. Either one leaks the
    # director's filesystem layout and often their username.
    ABS_PATH = re.compile(r'(?:[A-Za-z]:\\\\|[A-Za-z]:\\|/home/|/Users/)')

    def test_run_ledger_carries_no_retired_identity_or_local_path(self):
        root = os.path.dirname(HERE)
        runs = os.path.join(root, "runs")
        if not os.path.isdir(runs):
            self.skipTest("no runs/ directory in this checkout")
        offenders = []
        seen = 0
        for dirpath, _, files in os.walk(runs):
            for name in sorted(files):
                if not name.endswith(".md"):
                    continue
                seen += 1
                p = os.path.join(dirpath, name)
                text = open(p, encoding="utf-8").read()
                rel = os.path.relpath(p, root)
                low = text.lower()
                for ident in self.RETIRED:
                    if ident in low:
                        offenders.append(f"{rel}: retired identity {ident!r}")
                m = self.ABS_PATH.search(text)
                if m:
                    offenders.append(f"{rel}: absolute local path near {m.group(0)!r}")
        self.assertTrue(seen, "runs/ contains no markdown — the check would pass vacuously")
        self.assertEqual([], offenders,
                         "PUBLIC repo (DECISION_LEDGER D004): redact before committing —\n  "
                         + "\n  ".join(offenders))

class EncodingGuard(unittest.TestCase):
    """F3 (DEBT_LEDGER D-5, repaid): every output tool guards stdout AND stderr
    against a non-UTF-8 console via the single shared tools/_encoding.py — not an
    inline copy. stderr matters: four tools used to guard stdout only, so a
    non-ASCII error (e.g. "§") crashed on write to a cp1252 stderr.
    """

    OUTPUT_TOOLS = ("verdict-lint.py", "run-trace.py", "stop-gate.py",
                     "structure-report.py", "graph-audit.py", "registry-check.py")

    def test_every_output_tool_imports_the_shared_guard_and_no_copy_survives(self):
        missing = [n for n in self.OUTPUT_TOOLS
                   if "from _encoding import utf8_streams"
                   not in open(os.path.join(HERE, n), encoding="utf-8").read()]
        self.assertEqual([], missing, "no longer import _encoding: " + ", ".join(missing))
        offenders = [n for n in os.listdir(HERE)
                     if n.endswith(".py") and n not in ("_encoding.py", "test_tools.py")
                     and "reconfigure" in open(os.path.join(HERE, n), encoding="utf-8").read()]
        self.assertEqual([], offenders, "inline reconfigure copy outside _encoding.py: "
                         + ", ".join(offenders))

    def test_tool_stderr_survives_a_cp1252_console(self):
        env = dict(os.environ, PYTHONIOENCODING="cp1252")
        for name in ("verdict-lint.py", "graph-audit.py"):
            p = subprocess.run([sys.executable, os.path.join(HERE, name), "--help"],
                               capture_output=True, text=True, env=env)
            self.assertNotIn("UnicodeEncodeError", p.stderr, f"{name}: {p.stderr[-500:]}")

class SkillFrontmatter(unittest.TestCase):
    """F1: every skill's trigger description must be short (harness truncates a long
    aggregate) AND safe YAML — a bulk edit once flattened evolve-maintain's
    description to a bare scalar containing "system: bug reports", a colon-space
    that is a YAML mapping separator in plain-scalar context (hard parse error).
    Block-scalar form (`description: >`) sidesteps the hazard; checked stdlib-only.
    """

    FRONTMATTER_RE = re.compile(
        r'^---\nname: (\S+)\ndescription: >\n((?:  .*\n)+)---\n')

    def _skills(self):
        root = os.path.dirname(HERE)
        return sorted(e.name for e in os.scandir(os.path.join(root, "skills")) if e.is_dir())

    def test_every_skill_uses_safe_block_scalar_description(self):
        root = os.path.dirname(HERE)
        bad = []
        for name in self._skills():
            path = os.path.join(root, "skills", name, "SKILL.md")
            text = open(path, encoding="utf-8").read()
            if not self.FRONTMATTER_RE.match(text):
                bad.append(name)
        self.assertEqual([], bad,
                         "these skills' frontmatter is not `description: >` block-scalar "
                         "form — a plain-scalar colon-space (e.g. \"system: bug reports\") "
                         "is a YAML parse error, and the harness silently drops the whole "
                         "skill's trigger text: " + ", ".join(bad))

    def test_description_lengths_stay_under_budget(self):
        root = os.path.dirname(HERE)
        over, total = [], 0
        for name in self._skills():
            path = os.path.join(root, "skills", name, "SKILL.md")
            text = open(path, encoding="utf-8").read()
            m = self.FRONTMATTER_RE.match(text)
            if not m:
                continue  # reported by the sibling test
            folded = " ".join(line.strip() for line in m.group(2).splitlines())
            total += len(folded)
            limit = 400 if name == "chief-engineer" else 250
            if len(folded) > limit:
                over.append(f"{name} ({len(folded)} > {limit})")
        self.assertEqual([], over,
                         "F1: description exceeds its trigger-text budget: " + ", ".join(over))
        self.assertLessEqual(total, 5000,
                             f"F1: aggregate description budget exceeded ({total} > 5000)")


if __name__ == "__main__":
    unittest.main()
