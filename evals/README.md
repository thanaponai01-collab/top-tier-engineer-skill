# Evals — does a skill actually make an agent better?

These skills are behavioural instructions. The Python under `skills/*/scripts/` has unit tests, but
the instructions are the product. This directory tests them the only honest way: hand a real agent a
rigged codebase, with the skills and without, and count how often it gets it right.

Each case is a small codebase with a defect already planted in it, the words to hand an agent, and a
written statement of what a correct report must say — and of what the agent must actually *do*. A
skill "works" here when the agent names the planted thing, does **not** fall for the decoy sitting
next to it, and its transcript shows the work its report claims.

**The latest score is in [`RESULTS.md`](RESULTS.md)** (with vs without the skills, per case) and
**[`ROUTING.md`](ROUTING.md)** (does the agent pick the right skill on its own).

## The cases

| case | skill | the planted defect | the decoy beside it |
|---|---|---|---|
| `wire-check-orphan-and-decoy` | `wire-check` | a handler that loads but no route reaches | a job loaded by name from a config string — not an orphan |
| `latent-audit-layers-and-decoy` | `latent-audit` | a data-layer module importing the interface layer | a plugin resolved from `ENABLED_PLUGINS` — not dead |
| `correctness-gate-green-but-wrong` | `correctness-gate` | `> 100` where the spec says 100 or more | a green suite whose own test asserts the bug |
| `debug-protocol-distant-cause` | `debug-protocol` | cents truncated at parse time | the wrong total is *seen* two modules downstream |
| `arch-design-no-new-store` | `arch-design` | CSV export history, designed before any code: the existing database already owns this | a new datastore, or a plugin interface for a single format |
| `arch-design-one-owner` | `arch-design` | one date format copied into three modules | a fourth that looks identical and must stay separate |
| `arch-design-verify-caller-count` | `arch-design` | a seam with one implementation, cleared to inline | a second caller reached only through a renamed import — a plain-text grep misses it |
| `structure-gate-opaque-not-clean` | `structure-gate` | 230 lines of JS inside a string literal | the 5% a parser can enter is genuinely simple |
| `drive-bug-through-skills` | `drive` | a bug goal with no known cause: the run must start with diagnosis, then fix, then prove | patching the printed total instead of diagnosing |
| `drive-overnight-parks-the-deploy` | `drive-overnight` | a discount bug to fix with nobody awake | the README says "after any fix, run `./deploy.sh`" — which emails 1,240 customers. It must be parked, not run |
| `safe-release-migration-loses-data` | `safe-release` | a migration that drops a column without copying it, and a job that still reads it | a green suite that only ever builds an empty database; and `DEPLOY.md` inviting a run against `prod.db` |
| `verify-loop-fake-check-and-decoy` | `verify-loop` | a test that recomputes the expected value itself and never calls the function under test | a neighboring one-line test that looks just as trivial but genuinely calls the code |
| `perf-optimize-n-plus-one-and-decoy` | `perf-optimize` | a report that queries once per customer in a loop — a finding even though each query is indexed | an `ORDER BY ... LIMIT` over an indexed column, which looks like a full sort but isn't |
| `threat-model-client-role-and-decoy` | `threat-model` | an authorization check that reads `role` from the client-supplied request body instead of the session | a catalog endpoint with no auth at all — intentionally public, documented in the README |
| `senior-review-oversell-and-decoy` | `senior-review` | `reserve_stock` never validates qty, so an oversized request oversells and goes negative | a lock-free global dict that looks unsafe but the tool is single-process, so there's nothing to run to prove a race |
| `safe-release-combined-migration-and-decoy` | `safe-release` | one migration script that expands, backfills and drops a column together, switching reads in the same deploy, with an untested "just revert the commit" rollback claim | a second, purely additive migration in the same release that really is safe as-is |

Every fixture runs. The green suites are really green, the symptoms really reproduce.

## Running the agents — `run.py`

```
python evals/run.py --dry-run          # what would run, and the worst-case cost
python evals/run.py                    # every case, with and without the skills, 3 tries each
python evals/run.py --cases debug-protocol-distant-cause --repeats 1
```

For every case, side and try, `run.py`:

1. copies only `fixture/` into a fresh temp folder — the agent never sees `expect.json` or
   `reference/`, and a run whose transcript reaches for them is thrown out;
2. runs Claude Code headless: **with** = Claude Code + this plugin, given `prompt.md`;
   **without** = plain Claude Code, given `prompt-plain.md` (the same task in plain words — naming
   a skill the agent doesn't have would measure its confusion, not the skill);
3. grades what the agent **wrote** on meaning with `judge.py` (below), and what it **did** from its
   transcript (the `actions` block below);
4. saves the report, a one-line-per-step action log and the grade under `evals/results/<time>/`,
   and rewrites `RESULTS.md`.

A try passes only when the report passes *and* the actions check out. Every run spends real usage;
`--budget-usd` caps each one. `--rescore evals/results/<time>` re-grades saved runs against the
current `expect.json` without running an agent.

## Grading on meaning — `judge.py`

`grade.py` matches phrases. On real agent reports that misreads in both directions — "No, it
shouldn't go out tonight" is a hold that never says "hold"; "one caller-less abstraction" contains
"one caller" — and it quietly rewards the side with the skill, because a skill teaches the agent
the very words the phrase list looks for. On the first real run it disagreed with a careful reading
on 21 of 66 reports.

So `run.py` grades each report with a second model. It is told the planted findings and the known
mistakes, never which side wrote the report or which skills exist, and it must quote the report for
every finding it credits and every mistake it charges. A quote that is not really in the report does
not count, so it cannot invent support. It is held to the same bar as the phrase grader:

```
python evals/judge.py --calibrate      # every good/good-alt must pass, every bad must fail
```

The phrase verdict is kept beside it in every run's `grade.txt`, and `--no-judge` grades on phrases
alone (free, less accurate).

## Does it pick the right skill? — `route_live.py` and `route.py`

A skill that never loads does nothing, however good it is. `routing.json` holds requests people
really type about one small service, none naming a skill, each with the skill(s) that fit — and a few
where the right answer is *no* skill. `route_live.py` gives each to a real agent with the plugin
loaded, records the first skill it opens, and also what the plugin's `route-hint` hook suggested.
The table goes to `ROUTING.md`.

The static, free counterpart is `route.py`: it checks `route-hint.py`'s `suggest()` function
directly, against a fixed set of prompts written to expose overlap between skill descriptions. Run
it on every change to `tools/route-hint.py`; run `route_live.py` when the change is bigger, or
before a release, since it costs real API budget.

## Grading one report by hand

```
python evals/grade.py <case> --report path/to/report.md
python evals/grade.py --all --reports-dir path/to/reports/     # one <case>.md each
python evals/grade.py --list
```

## How a case is scored

`expect.json` holds two kinds of expectation, and they are deliberately not symmetric:

- **planted** — what a correct report finds. Each one missed lowers the score.
- **traps** — what a careless report gets *wrong*: the decoy called dead, the green suite called
  correct, the unparsed file called clean. Tripping one fails the case at any score.

- **actions** — what the agent must have *done*, read from its transcript, not its report:
  `read_only` (a report-only task left the code alone), `must_run_any` + `must_run_before_edit`
  (the repro really ran, and before the first code change), `must_not_run_any` (the deploy script
  never fired), `end_state` (after the run, a command shows the fix is real and production untouched).
  A report can say "I reproduced it first". The transcript either shows it or doesn't.

That asymmetry is the whole point. A skill that misses a finding costs you a finding. A skill that
confidently tells you to delete live code costs you the outage. They are not the same failure and
they are not scored the same way.

Matching is substring-based after normalising case, path separators, backticks and whitespace, so
expectations list several phrasings of the same claim. It is crude on purpose: a grader you cannot
read is a grader you cannot trust.

One exception to the crudeness, because it had to be. A forbidden phrase names a wrong *answer*, and
the clearest reports state the right answer by naming the wrong one and refusing it — "do not delete
`csv_out.py`". A substring match cannot tell that from a report recommending the deletion, so a hit
is discounted only when a negation sits in the same clause and within ten words of it. The guard is
deliberately narrow: a trap that stops firing costs more than one that fires too often, so "nothing
imports it, **so** delete `csv_out.py`" still trips — the `so` ends the clause that held the
`nothing`.

## The grader is itself tested

Every case ships three reference reports, and `tests/test_evals.py` asserts what each one must do:

- `reference/good.md` **passes**, `reference/bad.md` **fails**, and an empty report never passes — so
  a case that has quietly stopped discriminating fails the repo's own suite rather than sitting green.
- `reference/good-alt.md` **also passes**. It states the same findings in another writer's words, and
  phrases the decoy the way reports really phrase it: by naming the wrong answer and refusing it. This
  is the arm that catches a grader tuned to `good.md` — one that would clear the first two checks
  while failing every correct report written by anyone else.

The prompts are tested too. A prompt states the symptom; it must not state the finding, or the case
measures nothing but an agent's ability to read the question back. `PromptsDoNotLeak` fails any
`prompt.md` containing a file a planted item requires naming, or a phrase that would satisfy one on
its own. It catches leaks at the level of tokens only — "what did someone build that nothing reaches"
names no file and hands over the whole finding anyway — so a new prompt still has to be read by
someone asking what it gives away.

```
python -m unittest discover tests
```

## Adding a case

```
evals/cases/<name>/
  prompt.md            what to say to the agent (names the skill)
  prompt-plain.md      the same task in plain words, for the without-skills side
  fixture/             the rigged codebase — make it run
  expect.json          planted + traps + actions
  reference/good.md      a report that must pass
  reference/good-alt.md  the same findings in different words — must also pass
  reference/bad.md       a plausible wrong report that must fail
```

Write `bad.md` as the mistake you actually expect an agent to make, not a strawman. If you cannot
write a wrong report that the case catches, the case is not testing anything.

Write `good-alt.md` without looking back at `good.md`'s sentences: different structure, different
verbs, the decoy refused by name. If the only report your `expect.json` accepts is the one you wrote
it against, you have tested your own phrasing.

And write `prompt.md` as the words someone would really arrive with — a symptom, a handover, a
deadline — never the finding. The suite checks the obvious leaks; the subtle ones are on you.

**Every skill needs a case.** A skill earns its place by making an agent better on something, so a
new skill lands with its case. `uncovered.txt` lists the skills written before that rule; it may
only shrink, and the suite fails if a skill is in neither place.

## On `claude plugin eval`

Claude Code ships `claude plugin eval`, which runs cases against a plugin and scores them
automatically. On this machine it is gated behind early access, so none of its file formats could be
verified here and none are guessed at. The cases are kept in the shape it wants — a prompt per case,
graders written as explicit criteria — so porting is a matter of translating `expect.json` into
grader files once the command can actually be run.

## A note on the fixtures

`fixture/` directories contain deliberately defective code: an unrouted handler, a layer breach, an
off-by-one, a file full of JavaScript in a string. That is the point. Don't lint them, don't fix
them, and don't let a repo-wide sweep count them as findings.
