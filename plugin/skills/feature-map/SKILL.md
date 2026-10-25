---
name: feature-map
description: >-
  Map features to entry points and checks. Use for "what can this app do, how do I reach X?"
disable-model-invocation: true
metadata:
  stage: orient
  card: "what can this app do, how do I reach X?"
---

# Feature Map

An agent that does not know what a system has re-explores it every session, and drives it by
guessing. A feature map is the memory: what features exist, what each does, and the exact way in.
It earns trust only if it can be wrong loudly, so every entry point in it is something a script
can check against the code, and every feature says how it is known.

## What goes in a feature

One `##` section per feature in `FEATURES.md` at the repo root, inside the repository root you were
given. Each bullet is `key: value`:

```
## Checkout
- what: Pay for the cart and get an order id.
- route: `/checkout` @ src/routes.tsx
- click: `[data-testid=pay-btn]` @ src/Cart.tsx
- shortcut: `Ctrl+Enter` @ src/keys.ts :: submitOrder
- cli: `shop checkout` @ cli.py
- trace: `checkout` @ src/routes.tsx > `placeOrder` @ src/orders.ts > `orders` @ db/schema.sql
- verify: Checkout
- status: proven: drove /checkout in a browser, order id shown

## Not features
- click: `#debug-dump` @ src/Admin.tsx: developer dump, hidden in production builds
```

- **what:** what it does for its user, in one sentence, not what the code is called.
- **Entry points** (`route`, `click`, `shortcut`, `cli`, `menu`; `api` reads as `route`): every way in,
  as `` `anchor` @ file :: needle ``. `check` looks for the needle in that file as a whole token
  (`pay-btn` is not found in `pay-btn-v2`). It is derived from the anchor (the selector's value, the
  route's path, the subcommand); a shortcut must appear as the same combo in a quoted string. Write
  `:: needle` when that is not what the code contains. Prefer a stable anchor (a test-id attribute, an accessible
  name, an id) over a class or a position.
- **trace:** the path from entry point to effect, steps joined by ` > `, each `` `symbol` @ file ``
  (handler, then what it calls, then the row, file or request that changes). The first step is in an
  entry point's file or called from it, and each later step is referenced from the step before it,
  so an agent can follow the feature from where the user starts without searching.
- **verify:** when the repo has a VERIFY.md (`verify-loop`), the section that checks this feature.
  With no VERIFY.md, leave it out: the receipts from `prove` are the map's own proof.
- **status:** an evidence label, then how you know it. `proven` needs a receipt from `prove` (Build
  it, step 4) for every entry point, kept in `.features/<feature>.json` with a hash of each file the
  feature names; `check` calls it drifted once one of those files changes. A feature linked to a
  VERIFY.md section also needs that section's check seen rejecting a wrong product.
- Also worth a line when true: **needs** (login, a flag, a role, seeded data) and **effect** (what
  changes: a row, a file, a request).

*Evidence labels: **proven** = you ran it and it worked · **failing** = you ran it and it did
not (the failed run is recorded) · **traced** = you read the whole chain, start to end ·
**suspected** = none of these.*

**Not features:** an entry point the code declares that is not a feature (a debug control, a
test-only selector, an internal command) goes under `## Not features`, as an entry line with the
reason after it. It stops counting as unmapped only with a reason, and it is still checked, so it goes
stale like any other line when the code drops it. `## Not built` is prose and is not checked.

*Test:* an agent that has read only this file could open the feature, with no searching.

## Build it

1. **Draft from the code.** `python <this skill's base directory>/scripts/features.py init` lists
   the entry points it finds (server routes, page files, test-id attributes and button ids, accelerators
   and hotkeys, CLI subcommands) grouped by likely feature. It is a scan, not the map: it cannot see
   a click path built at runtime or a shortcut set in config.
2. **Trace each feature.** Follow it from the entry point to its effect and write the `trace:` path, reading
   every hop rather than guessing the middle. A hop you cannot follow is a finding, and the path stops there.
3. **Read the code behind each group and regroup by real feature.** Trace from where the system
   starts (router, menu template, CLI dispatcher). Add what the scan could not see. Where the map
   would need a guess, write `suspected` rather than a confident line.
4. **Prove the entry points by running them, through `prove`.** CLI or API:
   `python <base>/scripts/features.py prove --feature "<name>" -- <the command>` runs it in the repo
   and keeps the exit code and the end of its output. It proves the entry points whose word the
   command contains (`python notes.py export out.csv` proves `cli: export`, a `curl` of
   `/checkout` proves that route); name any other with `--entry "<kind>: <anchor>"`, spelled as the
   map line. Web or desktop: drive it, save the screenshot or response inside the repo, then
   `prove --feature "<name>" --entry "click: <anchor>" --file <it> --note "<what it shows>"`.
   `check` prints the exact `prove` line for every entry point still without a receipt. Every
   entry point of a `proven` feature needs a passing receipt; a route you read but did not hit is
   `traced`. A run that fails is kept as a failed receipt: it is a finding to report (an entry
   point that exists but crashes or does nothing), never a feature to label `proven`.
   An entry point that writes data runs with `--copy`, in a throwaway copy of the repo, so the
   person's data is never touched. One that sends, pays or deletes outside the repo stays
   `traced` unless the person says to run it, and a yes covers that one entry point.
5. **Only if the repo has a VERIFY.md, link each feature to it** (`verify-loop`): name its section,
   or add one, with a `path:` that covers every entry and trace file of the feature so
   `verify.py run --affected` reruns it when any of them changes; a `proven` feature then gets its
   receipt from `verify.py advance` until that says `done`. With no VERIFY.md, skip this step and
   do not create one: a map is not a request for a test suite.
6. **Check the map.** `python .features/features.py check --strict --rerun` must exit 0. `init` and
   `prove` keep this copy of the checker in `.features/` beside the receipts, so the next session,
   or CI, runs the same alarm without this skill installed. Commit `.features/` with the map, and
   add the line `check` prints to `AGENTS.md` or `CLAUDE.md` (creating `AGENTS.md` if neither
   exists), so the next agent is told the map is there.

A large app (about 15 features or more) is mapped by area: after `init`, give each area (a folder,
a router file, a CLI group) to its own agent where you can start agents. Each traces and proves its
features into `features/<area>.md`, and you keep `FEATURES.md` as the index of `include:` lines and
run `check` over the whole. Without agents, map the areas in batches, most-reached first. `--strict`
cannot pass until every entry point is mapped, so at the end of a batch run `check` without it, and
report the unmapped count as what is left instead of calling the map done.

*Test:* `check --strict --rerun` prints `0 stale | 0 broken | 0 untraced | 0 unmapped | 0 unlinked | 0 unlabeled | 0 undescribed | 0 drifted | 0 unproven | 0 unbacked | 0 unfenced | 0 unannounced | <n> not features | 0 regressed`.

## What `check` says

- **STALE**: a mapped entry point or trace step the code no longer has (renamed selector, moved route, deleted
  file). Fix the map or the code, whichever is wrong; never delete the line to make it green
  without finding out which.
- **BROKEN**: a trace step that exists but is not referenced from the step before it, so the path is
  no longer a real call chain (a renamed callee, a call removed, a call left only in a comment), or
  a first step that is neither in an entry point's file nor called from one. Re-trace that hop.
- **Untraced**: a feature with no `trace:` path.
- **Unmapped**: the code declares an entry point the map lacks: a feature nobody wrote down. If it
  is not a feature, list it under `## Not features` with the reason; never to make the count zero.
- **Unlinked, unlabeled, undescribed**: a feature with no status or no `what`; and, once the repo
  has a VERIFY.md, a feature with no section in it (or a `verify:` link to a VERIFY.md that is not
  there). Also lists VERIFY.md sections no feature links.
- **Drifted**: a `proven` feature with a file changed since its receipt was taken. Run
  `prove --again` (every recorded command re-run and re-recorded, or one feature with
  `--feature`); the new receipt is the only way back to green, so a relabel without a run stays
  red. A run that fails now is recorded as failing: relabel that feature `failing` and report it.
- **Unproven**: `proven` with no receipt for an entry point, a receipt whose run failed, or a
  screenshot that is missing or not the one recorded; or `failing` with no failed run recorded.
  Prove it, or label it `traced`.
- **Unannounced**: no `AGENTS.md` or `CLAUDE.md` at the repo root points at `FEATURES.md` and its
  `check`. Agents load those files at the start of a session and nothing else, so a map they are
  not told about is re-discovered from scratch. `check` prints the line to add.
- **Unbacked**: a `proven` feature whose VERIFY.md section has no `verify-loop` receipt of its check
  rejecting a wrong product, or whose check failed in the last `verify.py` run. Run
  `verify.py advance` until `done`; never relabel to `traced` to hide a failing check. Without
  `verify-loop` beside this skill, `check` says receipts were not checked and judges no feature.
- **Unfenced**: the linked VERIFY.md section has no `path:`, or names files of the feature outside
  it, so a change there would not rerun its check under `--affected`. Widen the `path:`.
- **Proof:** the closing line says which entry points ran in the repo, which in a throwaway copy,
  which are failing and which were never run. Put it in your report: it is how the person learns
  what was done to their data.
- **FAILS** (with `--rerun`): a recorded run that passed when proven exits non-zero now. The
  feature broke since it was mapped; report it, and fix the code or relabel after a new `prove`.
- `--strict` fails on every group after BROKEN too; without it only STALE, BROKEN and FAILS fail.
  Use `--strict --rerun` for "done". `not features` is a count to read, not a failure.

`check` alone reads code text, so it proves an entry point and each trace hop are *declared and
linked*, not that they *work*. `prove` is what makes an entry `proven`, and `--rerun` is what shows
it still works after the code moves.

## After a change

`python <base>/scripts/features.py impact` lists the features whose entry or trace files changed
(git diff against HEAD, plus untracked; `--base REF` or `--files a b` to choose) and the VERIFY.md
section to rerun for each. Changed code no feature names is a gap in the map, or shared code to
check by hand. Run those sections with `verify-loop`, then `prove --again` what you re-ran.

## Using the map

Read `FEATURES.md` first when asked to drive, test, document or change an app, and take the entry
point from it rather than searching. Before trusting it, run `python .features/features.py check
--rerun`: it names what moved and what stopped working since the map was written. If an entry in
it fails when you use it, fix the map in the same change and `prove` it again. After any change
that adds, renames or removes a route, control, shortcut or command, run `check`. It is the drift
alarm.

## Rules

- **The map records the running system.** A feature you expect the system to have, or one on the
  roadmap, does not go in. Say so in a `## Not built` section if it helps.
- **Never invent an entry point.** An anchor you did not see in the code or on screen is wrong until
  shown otherwise.
- **Keep it short.** One line per fact. A map too long to read is a map nobody opens.
- **Split by area past about 150 lines.** `FEATURES.md` becomes an index, one line per area:
  `- include: features/<area>.md (what the area covers)`, and each area's features move to that file
  verbatim. `check` and `impact` read through the includes. A session working on billing reads the
  index and `features/billing.md`, nothing else.

Mapping every feature to its checks is `verify-loop`; this map is the feature inventory its strict
green does not prove. This skill stands without it: without it, the file above is the whole job.
