# Skill merge analysis

Question: where can skills be merged or shortened without losing quality? Measured 2026-10-12 on
36 skills (`skills/*/SKILL.md`), baseline 476 tests green.

## What was measured [proven]
- Exact repeated sentences of 8+ words across all SKILL.md and references: 5, and only one is real
  boilerplate: the three-line evidence-label definition, repeated in 25 skills (about 900 words in
  total). It stays: `tests/test_standalone.py` requires each skill to define the labels it uses so a
  copied SKILL.md works alone.
- Shared 4-word phrases between the pairs that look like overlaps (smaller skill = 100%):

| Pair | Shared | Verdict |
|---|---|---|
| correctness-gate + wire-check | 6.4% | keep: distinct jobs (does it work / is it connected); `pick-skill` already warns not to run both on one slice |
| agent-evals + agent-prove | 4.1% | keep: before-the-agent task set and grader vs repeated-run proof; both have eval cases |
| onboard-system + project-foundation | 3.6% | keep: onboard already loads foundation instead of copying it |
| senior-review + scrutinize | 3.5% | keep: whole codebase vs one diff; `pick-skill` routes on that |
| explain + onboard-system | 3.2% | keep: explain changes nothing; onboard writes the context files |
| drive + drive-overnight | 2.5% | park: see below |
| latent-audit + structure-gate | 2.3% | park: see below |
| arch-map + arch-design | 0.8% | park: see below |
| project-setup + project-foundation | 0.8% | keep: BRIEF decision, setup writes instructions only, foundation writes context files |
| project-context + project-update | 0.7% | park: see below |
| recall + project-context | 0.7% | keep: recall rebuilds state from git and notes, context answers a question |

Conclusion: the skill text is not duplicated. Shortening by deleting repeated text finds nothing to
delete. The duplication that existed was in the lists around the skills, and that is fixed.

## Done on this branch (no public interface touched)
- README skill table: hand-kept, 55 prose rows -> generated from frontmatter by `tools/catalog.py`
  (the same source as `CATALOG.md`); a skill can no longer be added to one list and forgotten in another.
- Flows and the nine-checkpoint Relay: three copies (README, pick-skill, drive playbooks) -> README
  points at `skills/pick-skill`. `drive` keeps its own executable playbooks; its own text says its
  version wins on disagreement.
- README: 3012 -> about 1900 words; "Context that outlives the session", "Searchable project memory"
  and "Complete setup" were three overlapping sections and are now one.
- BRIEF.md says what the whole repo is and where each fact lives; BUILD.md is current state plus
  Next (release history moved to `BUILD.archive.md`, which is not read at session start); AGENTS.md
  points non-Claude agents at the same rules.

## Parked: needs the owner (skill names and /commands are the public interface)
Each of these changes a name users type or a routing description, so none was done overnight.

| Candidate | Proposal | Verdict | Cost / risk |
|---|---|---|---|
| drive-overnight into drive | Make unattended a mode of `drive`; drop one manual command | park | Saves one catalog line (listing is at its 5000/5000 cap). Loses a discoverable `/drive-overnight`; its case `drive-overnight-parks-the-deploy` would be re-pointed. |
| latent-audit + structure-gate | One `code-health` skill, two scripts | park | Both are script-backed code-shape checks; routes differ ("what can I delete" vs "is it spaghetti"). Needs the combined description to stay under the 160-char cap. |
| arch-map into arch-design | Diagrams become a reference inside arch-design | park | 4.61.0 just rebuilt arch-design around before/after pictures; arch-map is a standalone "draw what this change does". Merge only if routing evals show the pair confuses agents. |
| project-context + project-update | One `project-memory` skill, read and write modes | park | Frees one auto-invocable slot, but a read-only question must not load write rules. |

To approve any: say which, then the work is the SKILL.md move, `python tools/catalog.py --write`,
README/pick-skill name fixes, the affected eval case, a version bump and a CHANGELOG entry.

## Agent-friendliness: what to do next
- Run the live evals for the changed entry files (`python evals/run.py --cases <case>`); not run
  overnight because they consume account usage. Helper tests prove structure only.
- Each skill is 300-1500 words of prose. A short "Do / Check / Stop" skeleton at the top of the
  largest ones (pick-skill 1561, build-discipline 1549, project-foundation 1462, arch-map 1459)
  is the one shortening worth trying, but only with before/after eval runs; not done unmeasured.
