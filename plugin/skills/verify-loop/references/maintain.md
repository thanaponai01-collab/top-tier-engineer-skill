# Maintain a project verify skill

Use this mode for a periodic pass over a project's `.claude/skills/verify/` skill (from
[create mode](create.md)). Also use it when someone asks to audit the verify skill, or after
changes that may have moved what users touch. A feature map starts to rot as soon as the app
changes. The unit of rigor is the feature, not each sentence: read every feature from source and
drive every feature live once.

## Outcomes

Pick one and say which:

- **clean:** every feature got source and live coverage, and nothing needed changing.
- **changed:** one change set of proven map, harness or recipe corrections.
- **blocked:** coverage could not finish, or a proven fix cannot land safely. Say exactly what
  blocked it.

## Edit scope

You may freely edit the skill's prose and map: its SKILL.md, `features/`, the `fail-proof:` lines
in VERIFY.md, `## Blind spots`, and `login:`.

The checks are frozen: check commands, the helpers they name, `oracle:` files, `fail-signal:`
lines and the `## Run` commands. A harness repair to any of them needs fresh rejection proof.
Freeze it with `baseline` only after a person has reviewed it. This also applies to a section you
add. Never edit product code. Never change an expected result so that it matches the app.
Behavior that the map describes but the app no longer does is either map drift (fix the map) or a
product gap (report it).

## The pass

0. **Locate.** `verify.py skill-check <repo>`. If there is no skill, use create mode instead of
   making one up. In a monorepo, run one pass per package skill.
1. **Audit.** `verify.py maintain <repo>` is read-only. For each feature it prints an action:
   - `MAP`: the feature has no feature file.
   - `RE-PROVE`: there is no current rejection receipt.
   - `FIX`: the last run was red.
   - `RE-DRIVE`: the source it names changed since the last maintained commit.
   - `DRIVE`: nothing is flagged.

   It also prints `SHAPE` (index hygiene and the create-mode contract), `BASELINE` (checks
   changed since the freeze) and `UNCLAIMED` (changed files that no feature names). Adding or
   changing any check invalidates every rejection receipt, so after a harness change expect
   `RE-PROVE` on every feature. Churn is
   counted from the `last-maintained: <sha>` line in `features/README.md`; `--since REF`
   overrides it.
2. **Source read.** Read each feature file against the source, starting with the `RE-DRIVE` and
   `FIX` rows. Do this in parallel read-only subagents if your harness has them. Return the
   feature summary, its source entry points, likely drift with file:line citations or "none",
   and one live recipe. Readers never drive the app and never edit.
3. **Reconcile.** Fix index hygiene. Spot-check the cited drift, and do not re-prove claims that
   are clean. For each `UNCLAIMED` file, either cite the user-facing surface it adds and map it
   (a VERIFY.md section and a feature file, then [create](create.md) steps 2-4), or note why it
   is not user-facing.
4. **Live pass.** This step is required even when the source looks clean. `verify.py run`
   launches, doctors, runs every mapped check and stops. Then drive, by hand, the sub-features
   and entry points that the map lists and the checks skip. Follow the skill's own Launch model.
   Three things hold throughout:
   - Run the doctor before the first drive and after any surprise. Where the doctor cannot see
     the problem, reset or relaunch.
   - Evidence survives every cleanup. Check its named location; do not assume it.
   - Nothing you started outlives its use.

   A feature is `verified-unreachable` only when you name the missing prerequisite and the route
   you tried. If the map omits that prerequisite, that is drift.
5. **Triage** each finding ([triage](triage.md)):
   - Wrong user-POV text is map drift. Fix it.
   - Working behavior that the harness cannot drive is a harness gap. Fix it, prove it rejects,
     then re-drive it.
   - Broken behavior is a product gap. It stays red and goes in the report. Never paper over it
     in the map.
   - `RE-PROVE`: in a scratch copy, put the product in the `fail-proof:` state, see the
     `fail-signal:` from `verify.py run`, then restore.
6. **Finish.** `skill-check` must be ok. Run `baseline` only for check changes a person
   approved. If every feature got source and live coverage, set `last-maintained:` to the
   commit you audited. Then run `run --strict` and `report` last, so that the verdict covers the
   final files. Re-read each file you changed before handing over one change set. Next time,
   check inputs that match the baseline do not count as churn.

## Report

Lead with the outcome. Then give:

- the `verify.py report` answer ([format](handoff.md#what-comes-back));
- each feature with its action and live result;
- what drifted and what you changed;
- product gaps;
- unreachable features with their prerequisites;
- unmapped surfaces.

Keep scratch run notes out of the commit.
