# Design new, or replace a part

**Replace a part** when one area's foundation is wrong (its data model, or a core everything bends
around) and patching costs more than rebuilding: put a stable interface in front, move callers over
one at a time, delete the old path when none remain. Ask the user first; never propose replacing
the whole system unless asked.

**Design new**: first pin the numbers that decide shape (load, data size, latency, consistency, who
runs it). A missing one is assumed and labelled, never designed for "scale" in general. A structural
choice with no requirement behind it is *speculative*. Reuse what the codebase already owns before
adding anything (the reuse rule in SKILL.md applies in full).

Give module boundaries and contracts, not technologies: each module's one-sentence responsibility,
its data and error shapes, who may call whom, drawn as one diagram with plain labels. Then a
pre-mortem ("a year on, this failed: the three likeliest reasons") with a design change or an
accepted risk for each. Every structural choice still gets two real options and a door (SKILL.md,
step 4).
