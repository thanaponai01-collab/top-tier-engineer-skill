#!/usr/bin/env python3
"""
route.py — does `route-hint` name the right skill for a real prompt?

`tools/route-hint.py` only gets a vote on prompts nobody has already routed
themselves, so its accuracy is the whole product for that path. The existing
unit tests (`tests/test_hooks.py`) pin down the rules that already exist; this
file is the harder question — the prompts that expose *gaps* between skills
whose descriptions overlap (arch-design vs structure-gate, agent-* vs each
other, "done" the goal-word vs "done" the finished-work-word, and so on), the
kind of thing that shows up once you have more than a couple dozen skills.

Each case is (prompt, expected_skill_or_None). Run it:

    python evals/route.py

Exit code is 0 only if every case passes.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTE_HINT = ROOT / "tools" / "route-hint.py"

_spec = importlib.util.spec_from_file_location("route_hint", ROUTE_HINT)
route_hint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(route_hint)

# CASES that already had a dedicated rule before this eval existed — these
# establish that fixing the gaps below doesn't cost any of the routing that
# already worked.
ESTABLISHED = [
    ("the login page is broken", "debug-protocol"),
    ("login is broken because the token expires early", "evolve-maintain"),
    ("time to deploy this to prod", "safe-release"),
    ("can this endpoint be abused?", "threat-model"),
    ("file these as issues please", "issue-handoff"),
    ("find the dead code in here", "latent-audit"),
    ("is the new handler hooked up?", "wire-check"),
    ("honestly is this codebase spaghetti", "structure-gate"),
    ("second opinion on this PR before I merge", "scrutinize"),
    ("does this actually work?", "correctness-gate"),
    ("show me the architecture", "arch-map"),
    ("upgrade the dependencies", "evolve-maintain"),
    ("the report takes forever to load", "perf-optimize"),
    ("which skill should I use here", "pick-skill"),
    ("look at my codebase and tell me what to do", "senior-review"),
    ("why does the cache work this way?", "code-history"),
    ("walk me through how checkout works", "explain"),
]

# CASES that exposed a real gap: a skill exists, someone would plausibly type
# these words, and route-hint had no rule that reached it — so it fell
# silent (None) instead of naming the skill.
GAPS = [
    ("we have three separate places that all implement rate limiting, "
     "should they be one thing?", "arch-design"),
    ("should this be a queue or a synchronous call?", "arch-design"),
    ("is this over-engineered, too many layers?", "arch-design"),
    ("the checkout API is timing out under load and I don't know why",
     "debug-protocol"),
    ("can you map every feature to its shortcut and command", "feature-map"),
    ("make sure the agent checks its own work and loops until tests pass",
     "verify-loop"),
    ("we're building a model-driven feature, what checks do we need first",
     "agent-evals"),
    ("prove this agent still works after we swapped the prompt",
     "agent-prove"),
    ("one of the agent runs looks wrong, find where it diverged",
     "agent-trace"),
    ("we're shipping a live agent, how do we watch it", "agent-release"),
    ("nobody can agree on what done even means for this feature",
     "problem-framing"),
    ("carry this goal through to done, picking whatever skills it needs",
     "drive"),
    ("is the session handling secure", "threat-model"),
    ("what was I working on yesterday", "recall"),
    ("bootstrap the repo with the skills", "project-setup"),
]

CASES = ESTABLISHED + GAPS


def main():
    failures = []
    for prompt, expected in CASES:
        got = route_hint.suggest(prompt)[0]
        ok = got == expected
        print(("PASS" if ok else "FAIL") +
              "  %-70s -> want %-16s got %s" % (
                  prompt[:70], expected, got))
        if not ok:
            failures.append((prompt, expected, got))

    total = len(CASES)
    passed = total - len(failures)
    print("\n%d of %d" % (passed, total))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
