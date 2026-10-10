#!/usr/bin/env python3
"""
route-hint — names the skill a prompt is asking for, when nobody invoked one.

WHY THIS EXISTS
---------------
`pick-skill` is a router nobody reaches. A router is only invoked by someone who
already suspects a skill applies, and that person usually already knows which
one. So the routing that matters has to happen before anyone chooses anything —
on the prompt itself, from a hook that fires whether or not a skill was asked
for. That is this file. `pick-skill` keeps the job a hook genuinely cannot do:
telling five overlapping skills apart by reading the codebase.

PRECISION OVER RECALL
---------------------
A hook that fires on ordinary work gets uninstalled, and then it routes nobody
(the same reasoning that ruled out a blocking Stop hook — see unproven-gate.py).
So the rules here are deliberately narrow:

  * one suggestion per prompt, first match wins, most specific rule first;
  * each skill suggested at most once per session;
  * silence whenever the prompt already names a skill, or starts with `/`;
  * `build-discipline` is deliberately ABSENT. "build it" / "implement this" is
    the single most common thing anyone types; firing on it would make this hook
    constant noise, and its own description already matches that phrasing well.

Routing on what is KNOWN, not on the adjective, is why `debug-protocol` carries
a negative check: "broken, and here is why" is maintenance, not diagnosis.

Fails open, always. Exit 2 on UserPromptSubmit blocks the prompt AND ERASES IT,
so every error path here exits 0 with no output.

Usage:  UserPromptSubmit hook via hooks/hooks.json (payload on stdin)
        route-hint.py --selftest
"""
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

MAX_PROMPT = 20_000  # a pasted stack trace is not a routing question

# Every skill in this plugin, read from skills/ so a new or renamed skill needs
# no edit here. A prompt that already says one of these needs no help choosing,
# so the hook stays out of the way.
SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
try:
    SKILLS = tuple(sorted(p.name for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file()))
except OSError:
    SKILLS = ()
# Word-boundary matchers for SKILLS, so a prompt containing "driven" or
# "recalled" isn't mistaken for one that already named "drive" or "recall".
_SKILL_NAME_RE = tuple(
    (name, re.compile(r"\b" + re.escape(name) + r"\b", re.I)) for name in SKILLS
)

# Something is wrong, and the prompt does not say what.
#
# `error` is deliberately not matched on its own: "add error handling" is
# ordinary building, and routing it to diagnosis is exactly the kind of misfire
# that gets a hook uninstalled. It counts only where a failure is being
# reported — "getting an error", "the error says".
BROKEN = (r"\b(broken|breaks|failing|fails|crash\w*|throws?|throwing|"
          r"traceback|stack ?trace|not working|doesn.?t work|does not work|"
          r"won.?t work|stopped working|regression|hangs?|flaky|"
          r"timing out|timeouts?)\b"
          r"|\b(?:getting|got|an|the|this|that|same|weird|odd)\s+errors?\b"
          r"|\berror (?:message|says)\b")
# ...unless it does, in which case this is maintenance, not diagnosis.
CAUSE_KNOWN = (r"\b(because|caused by|root cause|the cause|i know why|"
               r"turns out|due to|the bug is|the problem is that)\b")

# (skill, trigger, veto, why this one). Order is the routing decision:
# the first rule that matches wins, so the specific ones come first.
RULES = (
    ("safe-release",
     r"\b(deploy|deploying|release it|ship it|push to prod\w*|cut a version|"
     r"migration|migrate the|alter table|backfill|schema change|"
     r"rename this column|drop the column)\b",
     None,
     "a release or a data change needs a way back before it runs"),

    ("threat-model",
     r"\b(secure|security|vulnerab\w+|exploit\w*|abused?|attacker|"
     r"injection|xss|csrf|ssrf|pen ?test|threat)\b",
     None,
     "it turns each abuse into a test instead of a checklist"),

    ("issue-handoff",
     r"\b(file (these |them |it )?as issues?|open an issue|make issues|"
     r"put (this|these) in (github|jira|linear)|create issues?)\b",
     None,
     "it files them without losing the proof line that made them buildable"),

    ("latent-audit",
     r"\b(dead code|unused (code|files?|components?|imports?)|"
     r"what can i delete|safe to delete|delete the unused)\b",
     None,
     "it proves code dead before anything is deleted"),

    ("wire-check",
     r"\b(hooked up|wired up|is it (connected|wired)|nothing happens|"
     r"isn.?t connected|what do we (actually )?serve|orphan\w*)\b",
     None,
     "it traces entry point inward, which is where the missing link shows"),

    ("structure-gate",
     r"\b(spaghetti|is this a mess|tangled|how messy|"
     r"structural(ly)? (bad|ok))\b",
     None,
     "it measures the shape and says how much it could not read"),

    ("scrutinize",
     r"\b(review this (pr|diff|plan)|second opinion|sanity[- ]check|"
     r"scrutini[sz]e|before i merge|does this look ok|should this land)\b",
     None,
     "it reads the change cold, including the code around the diff"),

    ("correctness-gate",
     r"\b(does (it|this) actually work|prove (it|this) works|"
     r"is (it|this) actually (right|correct)|test this properly|"
     r"are the tests any good)\b",
     None,
     "it checks whether the tests would catch a break, by breaking things"),

    ("arch-map",
     r"\b(show me the architecture|visuali[sz]e (the|this)|draw (the|this|me)|"
     r"architecture diagram|before and after diagram)\b",
     None,
     "every arrow it draws has a file:line behind it"),

    ("code-history",
     r"\bwhy (does|is|did|was|do) [^?.]{0,60}(work this way|built this way|"
     r"written this way|done this way|like this|hard-?coded)\b"
     r"|\bwhy did we (pick|choose|go with|use)\b"
     r"|\b(design rationale|post-?mortem|who decided)\b",
     None,
     "the reason lives in the records, and it says so when there is none"),

    ("onboard-system",
     r"\bonboard(ing)? (me )?(onto|to|into)\b"
     r"|\bget(ting)?( me)? up to speed on\b"
     r"|\bnever (seen|worked with) this (repo|codebase|system)\b"
     r"|\blearn this (codebase|system|repo) (top to bottom|from scratch|inside out)\b"
     r"|\bfirst (time|contact) (in|with) this (repo|codebase|system)\b",
     None,
     "it runs setup, the feature map, the architecture map and the why in one pass and leaves all of it behind"),

    ("project-setup",
     r"\b(set ?up|bootstrap|initiali[sz]e) (this|the|my|a) (new |fresh )?(project|repo|codebase) "
     r"(with|for) (the |these )?(skills|checks|verify)\b"
     r"|\bset ?up (the|these) skills\b|\bstart(ing)? fresh (here|with (the|these) skills)\b"
     r"|\bset ?up the checks\b",
     None,
     "it drafts the checks and leaves a pointer so the next session finds them"),

    ("drive-overnight",
     r"\bwhile i (sleep|am asleep|am away|'m away|.m asleep)\b"
     r"|\b(work|run|go|keep going|finish)( on)?( this| it)? (overnight|unattended)\b"
     r"|\brun (this )?(unattended|autonomously)\b",
     None,
     "it fixes the exit check and the budget first, then parks anything irreversible"),

    ("recall",
     r"\b(where were we|pick (this|it) back up|catch me up|"
     r"what was i (doing|working on)|where did i leave)\b",
     None,
     "it rebuilds the state from disk instead of from memory"),

    ("explain",
     r"\b(walk me through|teach me|help me understand|"
     r"explain (how|what) (the|this) (system|app|codebase|flow|module)|"
     r"how does (the|this) [\w -]{1,40}(subsystem|system|module|service|pipeline|layer|flow) work)\b",
     BROKEN,
     "it builds the picture at your pace and checks that it landed"),

    ("debug-protocol", BROKEN, CAUSE_KNOWN,
     "it proves the cause in both directions before anything is fixed"),

    ("evolve-maintain",
     BROKEN + r"|\b(upgrade|refactor|deprecat\w+|bump .*version)\b",
     None,
     "it classifies the change first, which is where maintenance damage starts"),

    ("perf-optimize",
     r"\b(slow|sluggish|laggy|clunky|takes forever|too long to load|"
     r"optimi[sz]e|speed (it|this) up|performance|n\+1|will (it|this) scale|"
     r"should i add an index)\b",
     None,
     "it changes nothing that a profile line did not point at"),

    ("pick-skill",
     r"\b(which skill|what skill|where do i start|where should i start|"
     r"what should i (do|run) (first|next))\b",
     None,
     "it names one skill and starts it, rather than listing the menu"),

    ("senior-review",
     r"\b(look at my (code|codebase|repo|project)|review (my|the) "
     r"(code|codebase|repo|project)|is (this|my) code (any )?good|"
     r"what should i fix (first|next)|is (it|this) production[- ]ready|"
     r"make (this|it) better)\b",
     None,
     "it answers the five questions with evidence and names the skill after it"),

    ("arch-design",
     r"\b(over-?engineered|too many layers|duplicat\w+ (systems?|logic|"
     r"implementations?)|should (this|these|it|they) be one (thing|module|"
     r"service)|queue or a (synchronous|cron|sync) |which (stack|pattern|"
     r"boundary) (should|to)|is the structure (itself )?wrong)\b",
     None,
     "it finds the duplicated system or the layer built for a future that never came"),

    ("feature-map",
     r"\b(map (every|each|the) feature|feature map|map .*(to (its |their )?"
     r"(shortcut|route|command))|which (shortcut|command)s? (map|correspond))\b",
     None,
     "it keeps every route, click and command mapped to the feature it serves"),

    ("verify-loop",
     r"\bchecks? its own work\b|\bloops? until (the )?tests? pass",
     None,
     "it closes the loop itself instead of stopping at green once"),

    ("agent-evals",
     r"\b(model-?driven feature|building an ai agent|what checks (do we need|"
     r"before))\b",
     None,
     "the checks come before the agent code, not after"),

    ("agent-prove",
     r"\bprove (this |the )?agent (still )?works\b|\bafter (we|you|i) swapped "
     r"the prompt\b|\b(model|prompt) (change|swap)\b",
     None,
     "it proves the agent still works over repeated runs, not just once"),

    ("agent-trace",
     r"\bagent runs? (look|looked)s? wrong\b|\bwhere (it|the run) diverged\b",
     None,
     "it finds the exact step where the run went wrong"),

    ("agent-release",
     r"\bshipping a live agent\b|\bwatch (a |the )?(live )?agent\b",
     None,
     "shipping an agent needs its own watch, not just a deploy"),

    ("problem-framing",
     r"\bwhat (done|finished) (even )?means\b|\bnobody (can|knows how to) "
     r"agree on\b",
     None,
     "it gets everyone to the same definition of done before anything is built"),

    ("plan-work",
     r"\b(plan (this|it|the work|the feature) out|break (this|it|the \w+) down (into|so)|"
     r"what can (safely )?(run|go) (at the same time|in parallel|together)|"
     r"(split|divide) (this|it|the work) (across|between|among) (agents|subagents|people)|"
     r"hand (the |these )?(pieces|parts|slices) (to|off to) (different|other|separate) agents)\b",
     None,
     "it gives every piece its own check and marks what can safely run together"),

    ("drive",
     r"\bcarry (this|the) goal through to done\b|\bcarry .* through to done\b",
     None,
     "it knows the goal but not yet the skills, and carries it through"),
)

COMPILED = tuple(
    (skill, re.compile(trigger, re.I),
     re.compile(veto, re.I) if veto else None, why)
    for skill, trigger, veto, why in RULES
)


def suggest(prompt):
    """(skill, why) for this prompt, or (None, None) when it needs no routing."""
    if not isinstance(prompt, str):
        return None, None
    text = prompt.strip()
    if not text or len(text) > MAX_PROMPT or text.startswith("/"):
        return None, None
    if any(pattern.search(text) for _, pattern in _SKILL_NAME_RE):
        return None, None  # they already named one
    for skill, trigger, veto, why in COMPILED:
        if trigger.search(text) and not (veto and veto.search(text)):
            return skill, why
    return None, None


def message(skill, why):
    """The one-line hint, or '' when there is nothing to say."""
    if not skill:
        return ""
    return (
        "[top-tier-engineer] This reads like a job for `%s` — %s.\n"
        "Optional guidance: use it if helpful, or continue directly. "
        "Skipping a skill needs no justification." % (skill, why)
    )


def _already_suggested(session_id, skill):
    """True if this skill was already suggested this session. Marks it if not."""
    if not session_id:
        return False
    key = hashlib.sha256(
        ("%s\0%s" % (session_id, skill)).encode("utf-8")
    ).hexdigest()[:32]
    marker = Path(tempfile.gettempdir()) / "tte-route-hint" / key
    try:
        if marker.exists():
            return True
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("", encoding="utf-8")
    except OSError:
        return True  # cannot dedupe: prefer silence to a hint every single turn
    return False


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0

    skill, why = suggest(payload.get("prompt"))
    if not skill or _already_suggested(payload.get("session_id"), skill):
        return 0

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        pass
    print(message(skill, why))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        assert suggest("the login page is broken")[0] == "debug-protocol"
        assert suggest("login broken because the token expires")[0] == "evolve-maintain"
        assert suggest("can this endpoint be abused?")[0] == "threat-model"
        assert suggest("time to deploy this to prod")[0] == "safe-release"
        assert suggest("what should I fix first?")[0] == "senior-review"
        assert suggest("where were we?")[0] == "recall"
        assert suggest("never seen this codebase before, get me up to speed on it")[0] == "onboard-system"
        assert suggest("break this down so other agents can take the pieces")[0] == "plan-work"
        assert suggest("add two numbers together")[0] is None
        assert suggest("run debug-protocol on this")[0] is None
        assert suggest("/pick-skill")[0] is None
        print("selftest ok")
        sys.exit(0)
    try:
        sys.exit(main())
    except BaseException:
        # Exit 2 here would erase the user's prompt. Never risk it.
        sys.exit(0)
