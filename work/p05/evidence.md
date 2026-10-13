# P05 bounded evidence

P05 adds an optional competing-design procedure to `arch-design`. It is triggered only for uncertain,
consequential choices; settled edits stay direct. This is one smoke campaign on two fixtures, not a
reliability, cost-saving, or model-diversity claim.

## Live trial

Command: `python evals/run.py --cases arch-design-competing-candidates arch-design-routine --repeats 1 --arms with --jobs 1 --budget-usd 2 --out evals/results/p05-final --no-scorecard`.

The runner used `claude-opus-5-5`. It opened `arch-design`; the consequential run also opened
`references/competing-designs.md`. No worker or second model was used. Results and transcripts are
retained in `evals/results/p05-final/`.

| Fixture | Pre-change baseline (without / with skill) | Final with skill | Final result |
|---|---:|---:|---|
| Consequential refund design | 3/5 / 4/5 | 5/5 | Pass: criteria before options, simplest viable synchronous design vs queue/worker alternative, selected tradeoff, one-way contract, honest same-session fallback and bounded exploration. |
| Routine settled label edit | 2/2 / 2/2 | 2/2 | Pass: direct one-file change, no candidate round or new boundary. |

Each final fixture ran once. The final runs cost $0.231 and $0.145 respectively and took 51.1 s and
13.6 s. The baseline used the same model and fixtures, with four runs totaling about $0.56. These
small samples do not establish reliability or savings. The result summaries were rejudged under the
final case expectations; the scorer revision accepted semantically explicit simplicity and bounded
options.

An intermediate replay after only adding the reference link scored 4/5 on the consequential fixture:
the agent did not state the criteria first and did not disclose the single-model fallback. Those cues
were moved into the main skill. The final action trace shows the linked reference was then opened.

## Grader and rejected attempt

The semantic judge and action checks passed both final runs. The phrase grader scored the final
consequential report 4/5 before its bound wording was aligned; it treated the lack of an exact
"bounded" phrase as an unbounded-arena trap despite the report stating two options, one session, no
workers/second model, $0.15 and a few minutes. The case now accepts "two options" and its good/bad
reference suite passes. The semantic judge remains the live meaning verdict.

The first draft of these cases had a prompt leak and mismatched reference wording. Its failed runner
and Drive records are retained under `evals/results/p05-baseline/` and `work/p05/runs/`; they are not
counted as acceptance evidence. Subsequent interrupted run records are also retained there.

## Repository proof

Focused eval-harness checks passed (44 tests). The first full-suite attempt ran 494 tests and retained
two failures: the P05 BUILD entry exceeded the 40-line limit, and the active RUN notice pushed the
front-door summary to 21 lines. The BUILD pointers were compacted and the hook now joins run status to
the project-context line, preserving both details. The failed run record is
`runs/RUN.p05-full-suite-failure.json`; the final full suite and catalog checks are recorded in the
current `RUN.json`. No release, installed-plugin update, or version bump was performed.
