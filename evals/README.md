# Evals — does a skill actually find the thing?

These skills are behavioural instructions. The Python under `skills/*/scripts/` has unit tests, but
the instructions are the product, and until now nothing tested them. This directory does.

Each case is a small codebase with a defect already planted in it, the words to hand an agent, and a
written statement of what a correct report must say. A skill "works" here when the report names the
planted thing — and does **not** fall for the decoy sitting next to it.

## The cases

| case | skill | the planted defect | the decoy beside it |
|---|---|---|---|
| `wire-check-orphan-and-decoy` | `wire-check` | a handler that loads but no route reaches | a job loaded by name from a config string — not an orphan |
| `latent-audit-layers-and-decoy` | `latent-audit` | a data-layer module importing the interface layer | a plugin resolved from `ENABLED_PLUGINS` — not dead |
| `correctness-gate-green-but-wrong` | `correctness-gate` | `> 100` where the spec says 100 or more | a green suite whose own test asserts the bug |
| `debug-protocol-distant-cause` | `debug-protocol` | cents truncated at parse time | the wrong total is *seen* two modules downstream |
| `arch-design-one-owner` | `arch-design` | one date format copied into three modules | a fourth that looks identical and must stay separate |
| `structure-gate-opaque-not-clean` | `structure-gate` | 230 lines of JS inside a string literal | the 5% a parser can enter is genuinely simple |

Every fixture runs. The green suites are really green, the symptoms really reproduce.

## Running one

1. Start an agent in `evals/cases/<case>/` and give it the words in `prompt.md`. It works on
   `fixture/`.
2. Save what it writes to a file.
3. Grade it:

```
python evals/grade.py <case> --report path/to/report.md
```

Or grade a whole run at once, with one `<case>.md` per case in a directory:

```
python evals/grade.py --all --reports-dir path/to/reports/
python evals/grade.py --list
```

Exit code is 0 only if every case passed. Stdlib only, nothing to install.

## How a case is scored

`expect.json` holds two kinds of expectation, and they are deliberately not symmetric:

- **planted** — what a correct report finds. Each one missed lowers the score.
- **traps** — what a careless report gets *wrong*: the decoy called dead, the green suite called
  correct, the unparsed file called clean. Tripping one fails the case at any score.

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
  prompt.md            what to say to the agent
  fixture/             the rigged codebase — make it run
  expect.json          planted + traps
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
